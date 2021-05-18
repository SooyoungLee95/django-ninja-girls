from enum import Enum

from ninja import Schema


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


class EventMsgRiderUpdated(Schema):
    event_id: str
    event_type: EventType
    id: int
    zone_id: int
    current_location: Location
    state: RiderState
