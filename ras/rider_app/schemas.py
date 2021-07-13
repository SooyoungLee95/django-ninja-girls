from typing import Any, Optional

from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from ninja.schema import Field, Schema
from pydantic import validator

from ras.rider_app.enums import PushAction
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


class MockRiderDispatch(Schema):
    rider_id: int = Field(alias="fleet_id")
    order_id: str
    pickup_delivery_relationship: str
    pickup_task_id: str = Field(alias="job_id")
    customer_comment: Optional[str] = Field(alias="job_description")
    estimated_pickup_time: str = Field(alias="job_pickup_datetime")
    pickup_restaurant_name: str = Field(alias="job_pickup_name")
    pickup_restaurant_phone_number: str = Field(alias="job_pickup_phone")
    estimated_delivery_time: str = Field(alias="job_delivery_datetime")
    pickup_restaurant_address: str = Field(alias="job_pickup_address")
    pickup_restaurant_picture_urls: list[str] = Field(alias="ref_images")
    custom_fields: list[Any]


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


class FcmPushPayload(Schema):
    title: str = "[Rideryo-BE] FCM Push Test title"
    body: str = "[Rideryo-BE] FCM Push Test body"
    registration_token: str
    action: PushAction
    id: str

    class Config:
        use_enum_values = True


class RiderProfile(Schema):
    full_name: str
    contract_type: str = Field(alias="ridercontract__contract_type")
    vehicle_name: str = Field(alias="ridercontract__vehicle_type__name")
