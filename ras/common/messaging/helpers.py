import logging
from functools import singledispatch, wraps

import boto3
from botocore.exceptions import BotoCoreError
from django.conf import settings

from ras.common.messaging.consts import RIDER_WORKING_STATE
from ras.common.messaging.schema import SNSMessage
from ras.rideryo.models import RiderAvailability
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
    pass


@publish_event.register
def publish_rider_working_state(instance: RiderAvailability, event_type: str):
    event_msg_cls = event_cls_to_type[event_type]
    event_msg = event_msg_cls(rider_id=instance.rider.pk, state="available" if instance.is_available else "unavailable")
    sns_message = SNSMessage(topic_arn=event_msg._arn, message=event_msg.json(exclude={"_arn"}))
    return publish_message(sns_message)


def publish_message(sns_message: SNSMessage):
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
