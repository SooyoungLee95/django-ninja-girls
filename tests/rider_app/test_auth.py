import json
from http import HTTPStatus
from unittest.mock import Mock, patch

import jwt
import pytest
from django.conf import settings
from django.test import Client
from django.urls import reverse
from pydantic import ValidationError

from ras.common.sms.helpers import send_sms_via_hubyo
from ras.rider_app.constants import AUTHYO_LOGIN_URL
from ras.rider_app.helpers import RIDER_APP_INITIAL_PASSWORD
from ras.rider_app.schemas import RiderLoginRequest
from tests.conftest import TEST_JWT_PRIVATE

client = Client()


def _call_login_api(input_body):
    return client.post(
        reverse("ninja:rider_app_login"),
        data=input_body.json(),
        content_type="application/json",
    )


@pytest.mark.django_db(transaction=True)
@patch("ras.rider_app.helpers.get_encrypted_payload", Mock(return_value="mock_token"))
def test_login_api_on_success_with_initial_password(rider_profile):
    # Given: 최초 패스워드를 사용하고 있는 라이더의 로그인 요청을 받고,
    input_body = RiderLoginRequest(email_address="test@test.com", password=RIDER_APP_INITIAL_PASSWORD)
    encrypted_payload = "mock_token"

    # When: login API를 호출하면,
    response = _call_login_api(input_body)

    # Then: HTTPStatus.OK 응답을 주어야 하고, authorization_url과 password_change_required는 True를 리턴해야한다
    data = json.loads(response.content)
    assert response.status_code == HTTPStatus.OK
    assert data["authorization_url"] == f"{AUTHYO_LOGIN_URL}?code={encrypted_payload}"
    assert data["password_change_required"] is True


@pytest.mark.django_db(transaction=True)
@patch("ras.rider_app.helpers.get_encrypted_payload", Mock(return_value="mock_token"))
def test_login_api_on_success_with_no_initial_password(rider_profile):
    # Given: rider의 password를 최초 패스워드가 아니도록 설정하고
    rider_account = rider_profile.rider
    rider_account.password = "new_password"
    rider_account.save()
    # And: 최초 패스워드를 사용하고있지 않은 라이더의 로그인 요청을 받은 후
    input_body = RiderLoginRequest(email_address="test@test.com", password="new_password")
    encrypted_payload = "mock_token"

    # When: login API를 호출하면,
    response = _call_login_api(input_body)

    # Then: HTTPStatus.OK 응답을 주어야 하고, authorization_url과 password_change_required는 False를 리턴해야한다
    data = json.loads(response.content)
    assert response.status_code == HTTPStatus.OK
    assert data["authorization_url"] == f"{AUTHYO_LOGIN_URL}?code={encrypted_payload}"
    assert data["password_change_required"] is False


@pytest.mark.django_db(transaction=True)
@patch("ras.rider_app.helpers.get_encrypted_payload", Mock(return_value="mock_token"))
def test_login_api_when_rider_never_agreed_on_service_agreements(rider_profile):
    # Given: 라이더의 로그인 요청을 받은 후
    input_body = RiderLoginRequest(email_address="test@test.com", password=RIDER_APP_INITIAL_PASSWORD)

    # When: login API를 호출하면,
    response = _call_login_api(input_body)

    # Then: HTTPStatus.OK 응답을 주어야 하고, checked_service_agreements 는 False를 반환한다.
    data = json.loads(response.content)
    assert response.status_code == HTTPStatus.OK
    assert data["checked_service_agreements"] is False


@pytest.mark.django_db(transaction=True)
@patch("ras.rider_app.helpers.get_encrypted_payload", Mock(return_value="mock_token"))
def test_login_api_when_rider_already_agreed_on_service_agreements(rider_profile, rider_service_agreements):
    # Given: 라이더의 로그인 요청을 받은 후
    input_body = RiderLoginRequest(email_address="test@test.com", password=RIDER_APP_INITIAL_PASSWORD)

    # When: login API를 호출하면,
    response = _call_login_api(input_body)

    # Then: HTTPStatus.OK 응답을 주어야 하고, checked_service_agreements 는 True를 반환한다.
    data = json.loads(response.content)
    assert response.status_code == HTTPStatus.OK
    assert data["checked_service_agreements"] is True


@pytest.mark.django_db(transaction=True)
def test_login_api_on_fail_with_invalid_email_address_format(rider_profile):
    with pytest.raises(ValidationError) as e:
        # When: 유효하지않은 email로 login API를 호출하면,
        _call_login_api(RiderLoginRequest(email_address="invalid_email_address", password="test_password"))
    # Then: 이메일이 유효하지 않음 에러 메세지가 리턴된다
    assert json.loads(e.value.json())[0]["msg"] == "이메일이 유효하지 않습니다."


@pytest.mark.django_db(transaction=True)
def test_login_api_on_fail_with_invalid_password(rider_profile):
    # When: 틀린 패스워드로 login API를 호출하면,
    response = _call_login_api(RiderLoginRequest(email_address="test@test.com", password="invalid_password"))

    # Then: HTTPStatus.BAD_REQUEST 상태코드와 패스워드가 일치하지 않습니다. 메세지를 리턴한다
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert json.loads(response.content)["message"] == "패스워드가 일치하지 않습니다."


@pytest.mark.django_db(transaction=True)
def test_login_api_on_fail_with_invalid_request_body(rider_profile):
    # Then: ValidationError를 발생시킨다
    with pytest.raises(ValidationError):
        # When: 유효하지않은 request body로 login API 요청을 하면,
        invalid_request_body = {"email": "test@test.com", "passwd": "testpasswd"}
        _call_login_api(RiderLoginRequest(**invalid_request_body))


class TestJWTAuthentication:
    def _call_test_api(self, token):
        return client.get(
            reverse("ninja:test_authentication"),
            content_type="application/json",
            **{"HTTP_AUTHORIZATION": f"Bearer {token}"},
        )

    def test_jwt_auth_on_invalid_token(self):
        invalid_jwt_token = "invalid_jwt_token"
        response = self._call_test_api(token=invalid_jwt_token)
        assert response.status_code == HTTPStatus.UNAUTHORIZED

    def test_jwt_auth_on_invalid_payload(self):
        token_with_invalid_payload = jwt.encode({"role": "owner"}, TEST_JWT_PRIVATE, algorithm="RS256")
        response = self._call_test_api(token=token_with_invalid_payload)
        assert response.status_code == HTTPStatus.UNAUTHORIZED

    @pytest.mark.django_db(transaction=True)
    def test_jwt_auth_on_invalid_rider_id_does_not_exist(self):
        token_with_invalid_rider_id = jwt.encode(
            {
                "iat": 1625703402,
                "exp": 16257034020,
                "sub_id": 12345,  # invalid rider_id does not exist
                "platform": settings.RIDERYO_BASE_URL,
                "base_url": settings.RIDERYO_ENV,
                "role": "rider",
            },
            TEST_JWT_PRIVATE,
            algorithm="RS256",
        )
        response = self._call_test_api(token=token_with_invalid_rider_id)
        assert response.status_code == HTTPStatus.UNAUTHORIZED

    def test_jwt_auth_on_expired_token(self):
        expired_token = jwt.encode(
            {
                "iat": 1625703402,
                "exp": 1625703402,  # expired
                "sub_id": 1,
                "platform": settings.RIDERYO_BASE_URL,
                "base_url": settings.RIDERYO_ENV,
                "role": "rider",
            },
            TEST_JWT_PRIVATE,
            algorithm="RS256",
        )
        response = self._call_test_api(token=expired_token)
        assert response.status_code == HTTPStatus.UNAUTHORIZED

    @pytest.mark.django_db(transaction=True)
    def test_jwt_auth_on_valid_token_and_payload(self, mock_jwt_token):
        response = self._call_test_api(token=mock_jwt_token)
        assert response.status_code == HTTPStatus.OK


class TestSendSMSViaHubyoClient:
    @patch("ras.common.sms.helpers.hubyo_client.send")
    def test_verification_code_via_sms_on_success(self, mock_send):
        # Given: SMS를 보내기 위한 유효한 정보가 주어지고,
        valid_infos = {
            "event": "send_sms",
            "entity": "sms",
            "tracking_id": "01073314120",
            "msg": {
                "data": {
                    "target": "01073314120",
                    "text": "test mock 인증번호는 1122334 입니다",
                    "sender": "1661-5270",
                    "is_lms": False,
                    "lms_subject": "",
                }
            },
        }
        # And: 정상적인 응답으로 주는 것을 세팅하고
        mock_send.return_value = {
            "MessageId": "2772c9a1-8f60-567d-af8a-90daa21f7134",
            "ResponseMetadata": {
                "HTTPStatusCode": 200,
            },
        }

        # When: SMS 전달 요청을 호출 하면,
        response = send_sms_via_hubyo(valid_infos)

        # Then: 응답의 상태 값으로 200을 받아야 한다
        assert response["ResponseMetadata"]["HTTPStatusCode"] == HTTPStatus.OK

    def test_verification_code_via_sms_with_missing_tracking_id(self):
        # Given: SMS를 보내기 위한 유효하지 않은 정보가 주어지고,
        invalid_infos = {
            "event": "send_sms",
            "entity": "sms",
            "tracking_id": "",  # tracking_id를 빈 값으로 처리
            "msg": {
                "data": {
                    "target": "01073314120",
                    "text": "test mock 인증번호는 1122334 입니다",
                    "sender": "1661-5270",
                    "is_lms": False,
                    "lms_subject": "",
                }
            },
        }

        # When: SMS 전달 요청을 호출 하면,
        response = send_sms_via_hubyo(invalid_infos)

        # Then: 응답의 상태 값으로 빈 값 받아야 한다.
        assert response == {}

    @patch("ras.common.sms.helpers.hubyo_client.send", Mock(side_effect=Exception))
    def test_verification_code_via_sms_with_unexpected_error(self):
        # Given: SMS를 보내기 위한 유효하지 않은 정보가 주어지고,
        valid_infos = {
            "event": "send_sms",
            "entity": "sms",
            "tracking_id": "01073314120",
            "msg": {
                "data": {
                    "target": "01073314120",
                    "text": "test mock 인증번호는 1122334 입니다",
                    "sender": "1661-5270",
                    "is_lms": False,
                    "lms_subject": "",
                }
            },
        }

        # When: SMS 전달 요청을 호출 하면,
        response = send_sms_via_hubyo(valid_infos)

        # Then: 응답의 상태 값으로 빈 값 받아야 한다.
        assert response == {}


class TestSendVerificationCodeViaSMSView:
    @pytest.mark.django_db(transaction=True)
    def test_send_verification_code_via_sms_view_on_success(self, rider_profile):
        # Given: DB에 존재하는 phone_number가 주어지고,
        valid_phone_number = {"phone_number": rider_profile.phone_number}

        # When: 인증요청 API를 호출 했을 때,
        response = client.post(
            reverse("ninja:send_verification_code_via_sms"),
            data=valid_phone_number,
            content_type="application/json",
        )

        # Then: 상태 코드 200을 리턴 해야한다.
        assert response.status_code == HTTPStatus.OK
