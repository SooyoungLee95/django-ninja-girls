import logging
from functools import singledispatch, wraps
from http import HTTPStatus
from typing import Callable, Optional

import boto3
import httpx
from botocore.exceptions import BotoCoreError
from django.conf import settings
from django.db import transaction
from ninja.errors import HttpError

from ras.common.messaging.consts import RIDER_WORKING_STATE
from ras.common.messaging.schema import SNSMessageForPublish, SNSMessageForSubscribe
from ras.rideryo.enums import DeliveryState
from ras.rideryo.models import (
    RiderAvailability,
    RiderDeliveryCancelReason,
    RiderDeliveryStateHistory,
    RiderDispatchRequestHistory,
)
from ras.rideryo.schemas import EventMsgRiderWorkingState

logger = logging.getLogger(__name__)
sns_client = boto3.client(
    "sns",
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_REGION,
    endpoint_url=settings.AWS_SNS_ENDPOINT_URL,
)
event_cls_to_type = {RIDER_WORKING_STATE: EventMsgRiderWorkingState}


@singledispatch
def publish_event(instance, event_type):
    raise NotImplementedError("publish_event must be implemented.")


@publish_event.register
def publish_rider_working_state(instance: RiderAvailability, event_type: str):
    event_msg_cls = event_cls_to_type[event_type]
    event_msg = event_msg_cls(rider_id=instance.rider.pk, state="available" if instance.is_available else "unavailable")
    sns_message = SNSMessageForPublish(topic_arn=event_msg._arn, message=event_msg.json(exclude={"_arn"}))
    return publish_message(sns_message)


def publish_message(sns_message: SNSMessageForPublish):
    try:
        return sns_client.publish(**sns_message.dict(exclude_none=True, exclude_unset=True))
    except BotoCoreError as e:
        logger.critical(f"[SNS] publish error {e!r}")
        return None


def trigger_event(event_type: str):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            instance = func(*args, **kwargs)
            publish_event(instance, event_type)
            return instance

        return wrapper

    return decorator


def handle_order_cancelled_notification(sns_message: SNSMessageForSubscribe) -> Optional[RiderDispatchRequestHistory]:
    message = sns_message.message
    if not (rider_id := message["rider_id"]):
        return None

    order_id = message["order_id"]
    with transaction.atomic():
        dispatch_request = RiderDispatchRequestHistory.objects.get(order_id=order_id, rider_id=rider_id)
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
