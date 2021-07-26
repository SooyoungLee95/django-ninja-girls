from enum import Enum

from django.conf import settings
from ninja import Schema


class Location(Schema):
    latitude: float
    longitude: float


class EventType(Enum):
    ADD = "add"
    UPDATE = "update"
    DELETE = "delete"
    WORKING_STATE = "working-state"


class EventMsg(Schema):
    _arn: str
    event_type: EventType


class EventMsgRiderWorkingState(EventMsg):
    _arn = settings.ARN_SNS_TOPIC_RIDER
    event_type = EventType.WORKING_STATE
    rider_id: int
    state: str
