from ninja.schema import Field, Schema


class RiderAvailability(Schema):
    rider_id: int = Field(..., gt=0)
    is_available: bool


class RiderDispatchResult(Schema):
    rider_id: int = Field(..., gt=0)
    order_id: str
    pickup_task_id: str
    delivery_task_id: str
