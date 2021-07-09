from enum import Enum

from ninja import Schema

from ras.common.messaging.consts import RIDER_TOPIC_ARN


class Location(Schema):
    latitude: float
    longitude: float


class RiderState(str, Enum):
    AVAILABLE = "available"
    COMPLETED = "completed"
    IN_TRANSIT = "in_transit"
    NEAR_PICKUP = "near_pickup"
    NEAR_DROPOFF = "near_dropoff"
    NOT_WORKING = "not_working"
    BREAK = "break"


class EventType(Enum):
    ADD = "add"
    UPDATE = "update"
    DELETE = "delete"
    WORKING_STATE = "working-state"


class EventMsg(Schema):
    _arn: str
    event_type: EventType


class EventMsgRiderWorkingState(EventMsg):
    _arn = RIDER_TOPIC_ARN
    event_type = EventType.WORKING_STATE
    rider_id: int
    state: str
