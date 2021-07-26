from http import HTTPStatus
from typing import Callable, Optional

import httpx
from django.conf import settings
from django.db import transaction
from ninja.errors import HttpError

from ras.common.messaging.schema import SNSMessageForSubscribe
from ras.rideryo.enums import DeliveryState
from ras.rideryo.models import (
    RiderDeliveryCancelReason,
    RiderDeliveryStateHistory,
    RiderDispatchRequestHistory,
)


def handle_order_cancelled_notification(sns_message: SNSMessageForSubscribe) -> Optional[RiderDispatchRequestHistory]:
    message = sns_message.message
    if not (rider_id := message["rider_id"]):
        return None

    order_id = message["order_id"]
    with transaction.atomic():
        dispatch_request = (
            RiderDispatchRequestHistory.objects.filter(order_id=order_id, rider_id=rider_id)
            .order_by("-created_at")  # 동일 라이더에게 재배차될 가능성이 있으므로 정렬 후 조회
            .first()
        )
        RiderDeliveryStateHistory.objects.create(
            dispatch_request=dispatch_request, delivery_state=DeliveryState.CANCELLED
        )
        RiderDeliveryCancelReason.objects.create(dispatch_request=dispatch_request, reason=message["reason"])
    return dispatch_request


SNS_NOTIFICATION_HANDLER_MAP: dict[str, dict[str, Callable]] = {
    settings.ARN_SNS_TOPIC_ORDER: {
        "cancelled": handle_order_cancelled_notification,
    }
}


def handle_sns_notification(message_type: Optional[str], sns_message: SNSMessageForSubscribe):
    if message_type == "Notification":
        event_handlers = SNS_NOTIFICATION_HANDLER_MAP[sns_message.topic_arn]
        handler_func = event_handlers[sns_message.message["event_type"]]
        return handler_func(sns_message)
    elif message_type == "SubscriptionConfirmation" and sns_message.subscribe_url:
        httpx.get(sns_message.subscribe_url)
    elif message_type == "UnsubscribeConfirmation":
        pass
    else:
        raise HttpError(HTTPStatus.BAD_REQUEST, "Unprocessable notification")
