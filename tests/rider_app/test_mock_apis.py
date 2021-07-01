import json

from django.test import Client
from django.urls import reverse

from ras.rider_app.constants import (
    MOCK_ENCRYPTED_PAYLOAD,
    MOCK_JWT_ACCESS_TOKEN,
    MOCK_JWT_REFRESH_TOKEN,
    MOCK_TOKEN_PUBLISH_URL,
)
from ras.rider_app.schemas import RiderLoginRequest

client = Client()


def test_mock_login_api_on_success():
    # When: mock login API를 호출하면,
    response = client.post(
        reverse("ninja:rider_app_login"),
        data=RiderLoginRequest(**{"email_address": "kwon1234@naver.com", "password": "password"}).json(),
        content_type="application/json",
    )

    # Then: 200 응답을 주어야 하고, authorization_url과 password_change_required는 True를 리턴해야한다
    data = json.loads(response.content)
    assert response.status_code == 200
    assert data["authorization_url"] == f"{MOCK_TOKEN_PUBLISH_URL}?code={MOCK_ENCRYPTED_PAYLOAD}"
    assert data["password_change_required"] == "False"


def test_mock_generate_token_api_on_success():
    # When: 가짜 토큰 생성 API를 호출하면,
    response = client.get(
        reverse("ninja:mock_token_generate"),
        data={"code": "sample_code"},
        content_type="application/json",
    )

    # Then: 200 응답을 주어야 하고, access token과 refresh token을 리턴해야한다
    data = json.loads(response.content)
    assert response.status_code == 200
    assert data["access_token"] == MOCK_JWT_ACCESS_TOKEN
    assert data["refresh_token"] == MOCK_JWT_REFRESH_TOKEN
