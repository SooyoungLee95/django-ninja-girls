from ninja.schema import Field, Schema

from ras.rideryo.enums import RiderResponse as RiderResponseEnum


class RiderAvailability(Schema):
    rider_id: int = Field(..., gt=0)
    is_available: bool


class RiderDispatchResponse(Schema):
    dispatch_request_id: int
    response: RiderResponseEnum
