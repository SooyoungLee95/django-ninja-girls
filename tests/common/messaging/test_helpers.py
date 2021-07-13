from http import HTTPStatus
from unittest.mock import Mock, patch

import orjson
import pytest
from ninja.errors import HttpError

from ras.common.messaging import SNSMessageForPublish, publish_message
from ras.common.messaging.helpers import (
    handle_order_cancelled_notification,
    handle_sns_notification,
)
from ras.common.messaging.schema import SNSMessageForSubscribe
from ras.rideryo.enums import DeliveryState
from ras.rideryo.models import RiderDeliveryCancelReason, RiderDeliveryStateHistory


@patch("ras.common.messaging.helpers.sns_client.publish")
def test_publish_message(mock_sns_publish):
    # Given: SNSMessageForPublish Schema로 정의된 message가 있고
    sns_message = SNSMessageForPublish(topic_arn="test-topic-arn", message='{"test-message": 123}')
    # And: sns publish 호출시 True를 반환하는 경우
    mock_sns_publish.return_value = True

    # When: message를 publish 하면
    result = publish_message(sns_message)

    # Then: 예상한 mock 결과가 반환되고,
    assert result is True
    # And: publish 요청인자는 미리 정의한 message 값들과 일치한다.
    mock_sns_publish.assert_called_once_with(TopicArn="test-topic-arn", Message='{"test-message": 123}')


def test_handle_sns_notification_event(notification_data):
    # Given: SNSMessageForSubscribe Schema로 정의된 message가 있고
    sns_message = SNSMessageForSubscribe.parse_obj(notification_data)
    message_type = sns_message.type

    # And: 이벤트 처리 함수를 mock 처리하고
    mock_handler = Mock()
    with patch.dict(
        "ras.common.messaging.helpers.SNS_NOTIFICATION_HANDLER_MAP",
        {sns_message.topic_arn: {sns_message.message["event_type"]: mock_handler}},
    ):
        # When: sns 이벤트 처리 함수를 실행하면,
        handle_sns_notification(message_type, sns_message)

        # Then: 정의된 sns 이벤트 처리 함수가 실행된다.
        mock_handler.assert_called_once()


def test_handle_sns_subscription_event(subscription_data):
    # Given: SNSMessageForSubscribe Schema로 정의된 message가 있고
    sns_message = SNSMessageForSubscribe.parse_obj(subscription_data)
    message_type = sns_message.type

    with patch("ras.common.messaging.helpers.httpx.get") as mock_get:
        # When: sns 이벤트 처리 함수를 실행하면,
        handle_sns_notification(message_type, sns_message)

        # Then: 구독 url를 호출하게 된다.
        mock_get.assert_called_once_with(sns_message.subscribe_url)


def test_handle_sns_unsubscription_event(unsubscription_data):
    # Given: SNSMessageForSubscribe Schema로 정의된 message가 있고
    sns_message = SNSMessageForSubscribe.parse_obj(unsubscription_data)
    message_type = sns_message.type

    with patch("ras.common.messaging.helpers.httpx.get") as mock_get:
        # When: sns 이벤트 처리 함수를 실행하면,
        handle_sns_notification(message_type, sns_message)

        # Then: 구독 url를 호출하지 않는다
        mock_get.assert_not_called()


def test_handle_sns_unknown_event(notification_data):
    # Given: SNSMessageForSubscribe Schema로 정의된 message가 있고
    sns_message = SNSMessageForSubscribe.parse_obj(notification_data)
    # And: type을 이상하게 수정한 후에
    message_type = "unknwon type"

    try:
        # When: sns 이벤트 처리 함수를 실행하면,
        handle_sns_notification(message_type, sns_message)
    except HttpError as e:
        # Then: HttpError 예외가 발생해서 응답이 반환된다.
        assert e.status_code == HTTPStatus.BAD_REQUEST
    else:
        raise AssertionError()


@pytest.mark.django_db(transaction=True)
def test_handle_order_cancelled_notification(rider_dispatch_request, notification_data):
    # Given: SNSMessageForSubscribe Schema로 정의된 주문취소 message가 있고
    sns_message = SNSMessageForSubscribe.parse_obj(notification_data)
    rider_id = rider_dispatch_request.rider.pk
    order_id = rider_dispatch_request.order_id
    reason = "restaurant_cancelled"

    sns_message.message_ = orjson.dumps(
        {"rider_id": rider_id, "order_id": order_id, "reason": reason, "event_type": "cancelled"}
    ).decode()

    # When: sns 이벤트 처리 함수를 실행하면,
    handle_order_cancelled_notification(sns_message)

    # Then: 배달 상태 CANCELLED 로 기록이 저장되고
    state_history = (
        RiderDeliveryStateHistory.objects.filter(dispatch_request=rider_dispatch_request)
        .order_by("-created_at")
        .first()
    )
    assert state_history.delivery_state == DeliveryState.CANCELLED

    # Then: 취소 사유가 저장된다.
    cancel_reason = (
        RiderDeliveryCancelReason.objects.filter(dispatch_request=rider_dispatch_request)
        .order_by("-created_at")
        .first()
    )
    assert cancel_reason.reason == reason
