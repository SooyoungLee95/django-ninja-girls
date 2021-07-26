import json
from http import HTTPStatus
from unittest.mock import Mock, patch

import jwt
import pytest
from django.conf import settings
from django.test import Client
from django.urls import reverse
from pydantic import ValidationError

from ras.rider_app.constants import AUTHYO_LOGIN_URL
from ras.rider_app.schemas import RiderLoginRequest
from ras.rider_app.views import RIDER_APP_INITIAL_PASSWORD
from tests.conftest import TEST_JWT_PRIVATE

client = Client()


def _call_login_api(input_body):
    return client.post(
        reverse("ninja:rider_app_login"),
        data=input_body.json(),
        content_type="application/json",
    )


@pytest.mark.django_db(transaction=True)
@patch("ras.rider_app.views.get_encrypted_payload", Mock(return_value="mock_token"))
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
@patch("ras.rider_app.views.get_encrypted_payload", Mock(return_value="mock_token"))
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
