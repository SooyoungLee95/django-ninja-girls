import json
from unittest.mock import Mock, patch

import pytest
from django.test import Client
from django.urls import reverse
from pydantic import ValidationError

from ras.rider_app.constants import AUTHYO_BASE_URL, AUTHYO_LOGIN_URL
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
@patch("ras.rider_app.views._generate_encrypted_token", Mock(return_value="mock_token"))
def test_login_api_on_success(rider_profile):
    input_body = RiderLoginRequest(email_address="test@test.com", password=RIDER_APP_INITIAL_PASSWORD)
    encrypted_payload = "mock_token"
    response = _call_login_api(input_body)
    data = json.loads(response.content)
    assert response.status_code == 200
    assert data["authorization_url"] == f"{AUTHYO_BASE_URL}{AUTHYO_LOGIN_URL}?code={encrypted_payload}"
    assert data["password_change_required"] == "True"


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    "email_address, password", [("INVALID_EMAIL", RIDER_APP_INITIAL_PASSWORD), ("test@test.com", "INVALID_PASSWORD")]
)
def test_login_api_on_fail_with_auth_info_is_not_matched(email_address, password, rider_profile):
    response = _call_login_api(RiderLoginRequest(email_address=email_address, password=password))
    assert response.status_code == 400


@pytest.mark.django_db(transaction=True)
def test_login_api_on_fail_with_invalid_request_body(rider_profile):
    with pytest.raises(ValidationError):
        invalid_request_body = {"email": "test@test.com", "passwd": "testpasswd"}
        _call_login_api(RiderLoginRequest(**invalid_request_body))
