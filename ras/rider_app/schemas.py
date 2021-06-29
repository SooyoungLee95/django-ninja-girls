from ninja.schema import Field, Schema

from ras.rideryo.enums import RiderResponse as RiderResponseEnum


class RiderAvailability(Schema):
    is_available: bool


class RiderDispatchResponse(Schema):
    dispatch_request_id: int
    response: RiderResponseEnum


class RiderDispatch(Schema):
    rider_id: int = Field(..., gt=0)
    order_id: str
    pickup_task_id: str
    delivery_task_id: str


class RiderLoginRequest(Schema):
    email_address: str
    password: str


class RiderLoginResponse(Schema):
    authorization_url: str
    password_change_required: str


class AuthorizationCode(Schema):
    platform: str = "rideryo-dev"
    role: str = "rider"
    sub_id: str
    base_url: str = "http://rideryo_base_url"
