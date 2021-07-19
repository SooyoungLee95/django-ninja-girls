from enum import Enum

from django.conf import settings
from ninja.schema import Schema


class Event(str, Enum):
    ORDER_CANCEL = "ORDER_CANCEL"


class DebugEventTriggerMessage(Schema):
    message: dict


event_to_topic = {Event.ORDER_CANCEL: settings.ARN_SNS_TOPIC_ORDER}
