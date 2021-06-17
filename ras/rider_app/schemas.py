from enum import Enum

from ninja.schema import Field, Schema


class RiderAvailability(Schema):
    rider_id: int = Field(..., gt=0)
    is_available: bool


class DispatchState(str, Enum):
    ACCEPTED = "ACCEPTED"
    DECLINE = "DECLINE"
    IGNORE = "IGNORE"
    CANCEL = "CANCEL"


class RiderDispatchResponse(Schema):
    dispatch_request_id: int
    response: DispatchState
