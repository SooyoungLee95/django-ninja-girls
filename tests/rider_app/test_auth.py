import json

from django.test import Client
from django.urls import reverse

from ras.rider_app.schemas import RiderLoginRequest

client = Client()


def test_login_api_on_success():
    input_body = RiderLoginRequest(email_address="test@test.com", password="testpassword121@")
    response = client.post(
        reverse("ninja:rider_app_login"),
        data=input_body.json(),
        content_type="application/json",
    )
    data = json.loads(response.content)
    assert response.status_code == 200
    assert data["authorization_url"] == "authorization_url"
    assert data["password_change_required"] == "True"
