import json
from http import HTTPStatus
from unittest.mock import Mock, patch

import jwt
import pytest
from django.conf import settings
from django.test import Client
from django.urls import reverse
from hubyo_client.client import HubyoClientError
from ninja.errors import HttpError
from pydantic import ValidationError

from ras.common.sms.helpers import send_sms_via_hubyo
from ras.rider_app.constants import (
    AUTHYO_LOGIN_URL,
    MSG_FAIL_SENDING_VERIFICATION_CODE,
    MSG_INVALID_VERIFICATION_CODE,
    MSG_NOT_FOUND_RIDER,
    MSG_SUCCESS_CHECKING_VERIFICATION_CODE,
    MSG_UNAUTHORIZED,
    VERIFICATION_CODE_TIMEOUT_SECONDS,
)
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
        input_phone_number = "01073314120"
        verification_code = "112233"
        message = f"[요기요라이더] 인증번호는 {verification_code} 입니다."
        # And: 정상적인 응답으로 주는 것을 세팅하고
        mock_send.return_value = {
            "MessageId": "2772c9a1-8f60-567d-af8a-90daa21f7134",
            "ResponseMetadata": {
                "HTTPStatusCode": 200,
            },
        }

        # When: SMS 전달 요청을 호출 하면,
        response = send_sms_via_hubyo(phone_number=input_phone_number, message=message)

        # Then: 응답의 상태 값으로 200을 받아야 한다
        assert response["ResponseMetadata"]["HTTPStatusCode"] == HTTPStatus.OK

    @patch("ras.common.sms.helpers.hubyo_client.send", Mock(side_effect=HubyoClientError))
    def test_verification_code_via_sms_with_hubyo_client_error(self):
        # Given: 유효한 인증코드와 message 가 주어질 떄,
        verification_code = "112233"
        message = f"[요기요라이더] 인증번호는 {verification_code} 입니다."
        # When: SMS 전달 요청을 호출 할 때, HubyoClientError가 발생하면,
        response = send_sms_via_hubyo(phone_number="01073314120", message=message)

        # Then: 응답의 상태 값은 None 이어야 한다
        assert response is None

    @patch("ras.common.sms.helpers.hubyo_client.send", Mock(side_effect=Exception))
    def test_verification_code_via_sms_with_unexpected_error(self):
        # Given: 유효한 인증코드와 message 가 주어질 떄,
        verification_code = "112233"
        message = f"[요기요라이더] 인증번호는 {verification_code} 입니다."

        # When: SMS 전달 요청을 호출 할 때, Internal Server Error 가 발생하면,
        response = send_sms_via_hubyo(phone_number="01073314120", message=message)

        # Then: 응답의 상태 값은 None 이어야 한다
        assert response is None


class TestSendVerificationCodeViaSMSView:
    def _call_send_verification_code_via_sms_api_with_token(self, valid_request_body, header=None):
        return client.post(
            reverse("ninja:send_verification_code_via_sms"),
            data=valid_request_body,
            content_type="application/json",
            **header,
        )

    def _call_send_verification_code_via_sms_api(self, valid_request_body):
        return client.post(
            reverse("ninja:send_verification_code_via_sms"),
            data=valid_request_body,
            content_type="application/json",
        )

    @patch("ras.rider_app.views.cache.set")
    @patch("ras.rider_app.views.generate_random_verification_code", Mock(return_value="112233"))
    @patch("ras.rider_app.views.send_sms_via_hubyo")
    @pytest.mark.django_db(transaction=True)
    def test_send_verification_code_via_sms_view_on_success(
        self, mock_send_sms_via_hubyo, mock_cache_set, rider_profile
    ):
        # Given: DB에 존재하는 phone_number가 주어지고,
        rider_phone_number = rider_profile.phone_number
        valid_request_body = {"email_address": rider_profile.rider.email_address, "phone_number": rider_phone_number}
        verification_code = "112233"
        message = f"[요기요라이더] 인증번호는 {verification_code} 입니다."

        # When: 인증요청 API를 호출 했을 때,
        response = self._call_send_verification_code_via_sms_api(valid_request_body)

        # Then: 상태 코드 200을 리턴 해야한다.
        assert response.status_code == HTTPStatus.OK
        # And: send_sms_via_hubyo를 호출 해야 한다
        mock_send_sms_via_hubyo.assert_called_once_with(rider_phone_number, message)
        # And: redis에 휴대폰 번호:인증코드를 key, rider_id를 value로 timeout 300 sec 로 저장되어야 한다
        key = f"{rider_phone_number}:{verification_code}"
        mock_cache_set.assert_called_once_with(key, rider_profile.rider_id, timeout=VERIFICATION_CODE_TIMEOUT_SECONDS)

    @patch("ras.rider_app.views.cache.set")
    @patch("ras.rider_app.views.generate_random_verification_code", Mock(return_value="112233"))
    @patch("ras.rider_app.views.send_sms_via_hubyo")
    @pytest.mark.django_db(transaction=True)
    def test_send_verification_code_via_sms_view_on_success_with_not_email_address_but_token(
        self, mock_send_sms_via_hubyo, mock_cache_set, rider_profile, mock_jwt_token
    ):
        # Given: DB에 존재하는 phone_number가 주어지고,
        rider_phone_number = rider_profile.phone_number
        # And: 유효한 request body 정보가 주어지고, - email을 제외하고 phone_number가 보내짐
        valid_request_body = {"phone_number": rider_phone_number}
        verification_code = "112233"
        message = f"[요기요라이더] 인증번호는 {verification_code} 입니다."

        # When: 인증요청 API를 호출 했을 때,
        response = self._call_send_verification_code_via_sms_api_with_token(
            valid_request_body, header={"HTTP_AUTHORIZATION": f"Bearer {mock_jwt_token}"}
        )

        # Then: 상태 코드 200을 리턴 해야한다.
        assert response.status_code == HTTPStatus.OK
        # And: send_sms_via_hubyo를 호출 해야 한다
        mock_send_sms_via_hubyo.assert_called_once_with(rider_phone_number, message)
        # And: redis에 휴대폰 번호:인증코드를 key, rider_id를 value로 timeout 300 sec 로 저장되어야 한다
        key = f"{rider_phone_number}:{verification_code}"
        mock_cache_set.assert_called_once_with(key, rider_profile.rider_id, timeout=VERIFICATION_CODE_TIMEOUT_SECONDS)

    @patch("ras.rider_app.views.cache.set")
    @pytest.mark.django_db(transaction=True)
    def test_send_verification_code_via_sms_view_with_not_email_address_but_token_on_invalid_token_error(
        self, mock_cache_set, rider_profile
    ):
        # Given: DB에 존재하는 phone_number가 주어지고,
        valid_request_body = {"phone_number": rider_profile.phone_number}
        # And: 유효하지 않은 토큰이 주어지면서,
        invalid_token = "invalid_token"

        # When: 인증요청 API를 호출 했을 때,
        response = self._call_send_verification_code_via_sms_api_with_token(
            valid_request_body, header={"HTTP_AUTHORIZATION": f"Bearer {invalid_token}"}
        )

        # Then: 상태 코드 401을 리턴 해야하고,
        assert response.status_code == HTTPStatus.UNAUTHORIZED
        # AND: 토큰이 유효하지 않습니다. 메세지를 리턴해야한다.
        assert json.loads(response.content)["message"] == MSG_UNAUTHORIZED
        # And: redis에 휴대폰 번호: 인증코드가 저장되지 않아야 한다
        mock_cache_set.assert_not_called()

    @patch("ras.rider_app.views.cache.set")
    @pytest.mark.django_db(transaction=True)
    def test_send_verification_code_via_sms_view_on_does_not_exist_phone_number(self, mock_cache_set, rider_profile):
        # Given: DB에 존재하는 phone_number가 주어지고,
        not_exist_phone_number = {"phone_number": "not_exist_phone_number"}

        # When: 인증요청 API를 호출 했을 때,
        response = self._call_send_verification_code_via_sms_api(not_exist_phone_number)

        # Then: 상태 코드 404을 리턴 해야한다.
        assert response.status_code == HTTPStatus.NOT_FOUND
        # AND: 라이더를 찾을 수 없습니다. 메세지를 리턴해야한다.
        assert json.loads(response.content)["message"] == MSG_NOT_FOUND_RIDER
        # And: redis에 휴대폰 번호: 인증코드가 저장되지 않아야 한다
        mock_cache_set.assert_not_called()

    @patch("ras.rider_app.views.cache.set")
    @patch("ras.rider_app.views.send_sms_via_hubyo")
    @patch("ras.rider_app.views.generate_random_verification_code", Mock(return_value="112233"))
    @pytest.mark.django_db(transaction=True)
    def test_send_verification_code_via_sms_view_on_unexpected_internal_server_error(
        self, mock_send_sms_via_hubyo, mock_cache_set, rider_profile
    ):
        # Given: DB에 존재하는 phone_number가 주어지고,
        rider_phone_number = rider_profile.phone_number
        valid_request_body = {"email_address": rider_profile.rider.email_address, "phone_number": rider_phone_number}
        verification_code = "112233"
        # And: send_sms_via_hubyo 내부에서 SMS 전달이 되지 않고 실패한 상황에서,
        mock_send_sms_via_hubyo.side_effect = HttpError(
            HTTPStatus.INTERNAL_SERVER_ERROR, MSG_FAIL_SENDING_VERIFICATION_CODE
        )

        # When: 인증요청 API를 호출 했을 때,
        response = self._call_send_verification_code_via_sms_api(valid_request_body)

        # Then: 상태 코드 500을 리턴 해야한다.
        assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
        # And: redis에 휴대폰 번호:인증코드를 key, rider_id를 value로 timeout 300 sec 로 저장되어야 한다
        key = f"{rider_phone_number}:{verification_code}"
        mock_cache_set.assert_called_once_with(key, rider_profile.rider_id, timeout=VERIFICATION_CODE_TIMEOUT_SECONDS)
        # And: 인증번호 SMS 전송에 실패 하였습니다. 메세지를 리턴해야한다
        assert json.loads(response.content)["message"] == MSG_FAIL_SENDING_VERIFICATION_CODE

    @pytest.mark.django_db(transaction=True)
    def test_send_verification_code_via_sms_view_should_return_401_unauthorized_not_raising_value_error(
        self, rider_profile, mock_jwt_token
    ):
        # Given: DB에 존재하는 phone_number가 주어지고,
        rider_phone_number = rider_profile.phone_number
        valid_request_body = {"email_address": rider_profile.rider.email_address, "phone_number": rider_phone_number}
        # And: 띄어쓰기가 포함된 유효하지 않은 jwt token이 주어지고,
        invalid_jwt_tokwn = "in valid jw t token"

        # When: 인증요청 API를 호출 했을 때,
        response = self._call_send_verification_code_via_sms_api_with_token(
            valid_request_body, header={"HTTP_AUTHORIZATION": f"Bearer {invalid_jwt_tokwn}"}
        )

        # Then: 상태 코드 401을 리턴 해야한다.
        assert response.status_code == HTTPStatus.UNAUTHORIZED


class TestCheckVerificationCode:
    def _call_check_verification_code(self, request_body):
        return client.post(
            reverse("ninja:check_verification_code"),
            data=request_body,
            content_type="application/json",
        )

    @patch("ras.rider_app.views.cache.get")
    def test_check_verification_code_should_return_400_bad_request_when_phone_number_redis_key_does_not_exist(
        self, mock_cache_get
    ):
        # Given: 유효하지 않은 request_body가 주어지고,
        invalid_request_body = {"phone_number": "invalid_phone_number", "verification_code": "valid_verification_code"}
        # And: cache.get 했을 때, 리턴 값이 None으로 세팅해주고,
        mock_cache_get.return_value = None

        # When: 휴대폰 번호 인증 요청 확인 API를 호출 했을 때,
        response = self._call_check_verification_code(invalid_request_body)

        # Then: 400 Bad Request 상태코드이어야 한다
        assert response.status_code == HTTPStatus.BAD_REQUEST
        # And: 인증번호가 일치하지 않습니다. 메세지를 리턴해야한다
        assert json.loads(response.content)["message"] == MSG_INVALID_VERIFICATION_CODE

    @patch("ras.rider_app.views.cache.get")
    @pytest.mark.django_db(transaction=True)
    def test_check_verification_code_should_return_200_ok_on_success(
        self, mock_cache_get, mock_token_for_resetting_password, rider_profile
    ):
        # Given: 유효한 request_body가 주어지고,
        valid_input_verification_code = "112233"
        valid_request_body = {"phone_number": "01011112222", "verification_code": valid_input_verification_code}
        # And: redis에서 리턴된 값이 request_body에 일치 하도록 세팅한 다음
        mock_cache_get.return_value = rider_profile.rider_id

        # When: 휴대폰 번호 인증 요청 확인 API를 호출 했을 때,
        response = self._call_check_verification_code(valid_request_body)

        # Then: 200 OK 상태코드이어야 한다
        assert response.status_code == HTTPStatus.OK
        # And: token과 인증이 완료되었습니다 메세지를 리턴해야한다.
        response = json.loads(response.content)
        assert response["message"] == MSG_SUCCESS_CHECKING_VERIFICATION_CODE
        assert response["token"] == mock_token_for_resetting_password
