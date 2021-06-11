from ninja.schema import Field, Schema


class RiderAvailability(Schema):
    rider_id: int = Field(..., gt=0)
    is_available: bool
