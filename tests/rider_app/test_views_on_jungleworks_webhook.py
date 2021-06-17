from unittest.mock import patch

import pytest
from django.db import DatabaseError
from django.test import Client
from django.urls import reverse

from ras.rider_app.schemas import RiderDispatch
from ras.rideryo.models import JungleWorksTaskHistory, RiderDispatchRequestHistory

client = Client()


def call_api(input_body):
    return client.post(
        reverse("ninja:rider_app_dispatch_request_webhook"),
        data=input_body.json(),
        content_type="application/json",
    )


@pytest.mark.django_db(transaction=True)
def test_rider_app_dispatch_request_webhook(rider_profile):
    # Given: 정글웍스로부터 배차완료 event를 받았을 때,
    input_body = RiderDispatch(rider_id=rider_profile.pk, order_id="1", pickup_task_id="1", delivery_task_id="1")

    # When: dispatch_request_webhook 를 호출 하면,
    call_api(input_body)

    # Then: RiderDispatchRequestHistory 와 JungleWorksTaskHistory 값이 생성되어야 한다
    assert RiderDispatchRequestHistory.objects.count() == 1
    assert JungleWorksTaskHistory.objects.count() == 1


@pytest.mark.django_db(transaction=True)
@patch("ras.rider_app.helpers.logger.error")
def test_rider_app_dispatch_request_webhook_on_404_error(rider_profile):
    # Given: 라이더의 프로필이 존재하지 않는 상태에서
    not_exist_rider_profile_id = 10000
    input_body = RiderDispatch(
        rider_id=not_exist_rider_profile_id, order_id="1", pickup_task_id="1", delivery_task_id="1"
    )

    # When: dispatch_request_webhook 를 호출 하면,
    response = call_api(input_body)

    # Then: status는 200, logger.error 가 호출 되어야 한다
    assert response.status_code == 200
    # And: RiderDispatchRequestHistory 와 JungleWorksTaskHistory 값은 생성되지 않아야 한다.
    assert RiderDispatchRequestHistory.objects.count() == 0
    assert JungleWorksTaskHistory.objects.count() == 0


@pytest.mark.django_db(transaction=True)
@patch("ras.rider_app.helpers.logger.error")
def test_rider_app_dispatch_request_webhook_on_database_error(mock_logger_error, rider_profile):
    # Given: 정글웍스로부터 배차완료 event를 받고,
    input_body = RiderDispatch(rider_id=rider_profile.pk, order_id="1", pickup_task_id="1", delivery_task_id="1")

    with patch("ras.rider_app.helpers.query_create_dispatch_request_with_task") as mock_query_create:
        # When: dispatch_request_webhook 호출 시에, DatabaseError 가 발생하면,
        mock_query_create.side_effect = DatabaseError()
        response = call_api(input_body)

    # Then: status는 200, logger.error 가 호출 되어야 한다
    assert response.status_code == 200
    mock_logger_error.assert_called_once()
    # And: RiderDispatchRequestHistory 와 JungleWorksTaskHistory 값은 생성되지 않아야 한다.
    assert RiderDispatchRequestHistory.objects.count() == 0
    assert JungleWorksTaskHistory.objects.count() == 0
