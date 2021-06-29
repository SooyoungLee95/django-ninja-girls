import json
from unittest.mock import Mock, patch

import pytest
from django.test import Client
from django.urls import reverse
from pydantic import ValidationError

from config.settings.local import AUTHYO
from ras.rider_app.constants import AUTHYO_LOGIN_URL
from ras.rider_app.schemas import RiderLoginRequest
from ras.rider_app.views import RIDER_APP_INITIAL_PASSWORD

client = Client()


def _call_login_api(input_body):
    return client.post(
        reverse("ninja:rider_app_login"),
        data=input_body.json(),
        content_type="application/json",
    )


@pytest.mark.django_db(transaction=True)
@patch(
    "ras.common.authentication.helpers.AuthyoTokenAuthenticator.get_encrypted_payload", Mock(return_value="mock_token")
)
def test_login_api_on_success_with_initial_password(rider_profile):
    input_body = RiderLoginRequest(email_address="test@test.com", password=RIDER_APP_INITIAL_PASSWORD)
    encrypted_payload = "mock_token"
    response = _call_login_api(input_body)
    data = json.loads(response.content)
    assert response.status_code == 200
    assert data["authorization_url"] == f"{AUTHYO.BASE_URL}{AUTHYO_LOGIN_URL}?code={encrypted_payload}"
    assert data["password_change_required"] == "True"


@pytest.mark.django_db(transaction=True)
@patch(
    "ras.common.authentication.helpers.AuthyoTokenAuthenticator.get_encrypted_payload", Mock(return_value="mock_token")
)
def test_login_api_on_success_with_no_initial_password(rider_profile):
    rider_account = rider_profile.rider
    rider_account.password = "new_password"
    rider_account.save()
    input_body = RiderLoginRequest(email_address="test@test.com", password="new_password")
    encrypted_payload = "mock_token"
    response = _call_login_api(input_body)
    data = json.loads(response.content)
    assert response.status_code == 200
    assert data["authorization_url"] == f"{AUTHYO.BASE_URL}{AUTHYO_LOGIN_URL}?code={encrypted_payload}"
    assert data["password_change_required"] == "False"


@pytest.mark.django_db(transaction=True)
def test_login_api_on_fail_with_invalid_email_address_format(rider_profile):
    with pytest.raises(ValidationError) as e:
        _call_login_api(RiderLoginRequest(email_address="invalid_email_address", password="test_password"))
    assert json.loads(e.value.json())[0]["msg"] == "이메일이 유효하지 않습니다."


@pytest.mark.django_db(transaction=True)
def test_login_api_on_fail_with_invalid_password(rider_profile):
    response = _call_login_api(RiderLoginRequest(email_address="test@test.com", password="invalid_password"))
    assert response.status_code == 400
    assert json.loads(response.content)["message"] == "패스워드가 일치하지 않습니다."


@pytest.mark.django_db(transaction=True)
def test_login_api_on_fail_with_invalid_request_body(rider_profile):
    with pytest.raises(ValidationError):
        invalid_request_body = {"email": "test@test.com", "passwd": "testpasswd"}
        _call_login_api(RiderLoginRequest(**invalid_request_body))
