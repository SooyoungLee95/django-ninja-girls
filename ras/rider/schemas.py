from enum import Enum
from uuid import UUID

from ninja import Schema
from pydantic import Field, validator

from .helpers import generate_event_id


class Location(Schema):
    lat: float
    lng: float


class RiderState(Enum):
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


class EventMsg(Schema):
    event_id: str = Field(default_factory=generate_event_id)
    event_type: EventType
    event_name: str

    @validator("event_id", pre=True)
    def check_event_id(cls, value: str):
        service, _, uuid = value.partition(":")
        if service == "ras" and UUID(uuid):
            return value
        raise ValueError("Invalid event_id")


class EventMsgRiderUpdated(EventMsg):
    id: int
    zone_id: int
    current_location: Location
    state: RiderState
