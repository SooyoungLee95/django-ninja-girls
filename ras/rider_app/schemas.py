from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from ninja.schema import Field, Schema
from pydantic import validator

from ras.rideryo.enums import DeliveryState
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

    @validator("email_address")
    def check_email_address_format(cls, input_email_address):
        try:
            validate_email(input_email_address)
        except ValidationError:
            raise ValueError("이메일이 유효하지 않습니다.")
        return input_email_address


class RiderLoginResponse(Schema):
    authorization_url: str
    password_change_required: bool


class AuthyoPayload(Schema):
    sub_id: int  # rider id
    platform: str = "rideryo-dev"
    role: str = "rider"
    base_url: str = "http://rideryo-dev"


class RiderDeliveryState(Schema):
    dispatch_request_id: int
    state: DeliveryState
