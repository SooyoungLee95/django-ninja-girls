import json
from unittest.mock import Mock, patch

import pytest
from django.test import Client
from django.urls import reverse

from ras.rider_app.schemas import RiderLoginRequest
from ras.rider_app.views import RIDER_APP_INITIAL_PASSWORD

AUTHYO_BASE_URL = "https://staging-authyo.yogiyo.co.kr"
AUTHYO_LOGIN_URL = "/api/v1/auth/authorize"

client = Client()


@pytest.mark.django_db(transaction=True)
@patch("ras.rider_app.views._generate_encrypted_token", Mock(return_value="mock_token"))
def test_login_api_on_success(rider_profile):
    input_body = RiderLoginRequest(email_address="test@test.com", password=RIDER_APP_INITIAL_PASSWORD)
    encrypted_payload = "mock_token"
    response = client.post(
        reverse("ninja:rider_app_login"),
        data=input_body.json(),
        content_type="application/json",
    )
    data = json.loads(response.content)
    assert response.status_code == 200
    assert data["authorization_url"] == f"{AUTHYO_BASE_URL}{AUTHYO_LOGIN_URL}?code={encrypted_payload}"
    assert data["password_change_required"] == "True"


@pytest.mark.django_db(transaction=True)
def test_login_api_on_fail_with_auth_info_is_not_matched(rider_profile):
    input_body = RiderLoginRequest(email_address="test@test.com", password="INITIAL_PASSWORD!@")
    response = client.post(
        reverse("ninja:rider_app_login"),
        data=input_body.json(),
        content_type="application/json",
    )
    assert response.status_code == 400
