import pytest
from django.test import Client
from django.urls import reverse

from ras.rider_app.schemas import RiderDispatchResult
from ras.rideryo.models import JungleWorksTaskHistory, RiderDispatchRequestHistory

client = Client()


@pytest.mark.django_db(transaction=True)
def test_rider_app_dispatch_request_webhook(rider_profile):
    # Given: 정글웍스로부터 배차완료 event를 받았을 때,
    input_body = RiderDispatchResult(rider_id=rider_profile.pk, order_id="1", pickup_task_id="1", delivery_task_id="1")

    # When: webhook_api_from_jungleworks 를 호출 하면,
    client.post(
        reverse("ninja:rider_app_dispatch_request_webhook"),
        data=input_body.json(),
        content_type="application/json",
    )

    # Then: RiderDispatchRequestHistory 와 JungleWorksTaskHistory 값이 생성되어야 한다
    assert RiderDispatchRequestHistory.objects.count() == 1
    assert JungleWorksTaskHistory.objects.count() == 1
