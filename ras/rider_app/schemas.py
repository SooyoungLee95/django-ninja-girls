from datetime import date
from typing import Any, Optional

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from ninja.schema import Field, Schema
from pydantic import validator

from ras.rider_app.constants import (
    CANCEL_REASON_ISSUE_MAP,
    CUSTOMER_ISSUE,
    RESTAURANT_ISSUE,
    SYSTEM_ISSUE,
)
from ras.rider_app.enums import PushAction, RideryoRole
from ras.rideryo.enums import DeliveryState
from ras.rideryo.enums import RiderResponse as RiderResponseEnum


class RiderAvailability(Schema):
    is_available: bool


class RiderBan(Schema):
    rider_id: int
    is_banned: bool


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
    platform: str = settings.RIDERYO_BASE_URL
    base_url: str = settings.RIDERYO_ENV
    role: str = RideryoRole.RIDER


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


class RiderProfileSummary(Schema):
    full_name: str
    contract_type: str = Field(alias="ridercontract__contract_type")
    vehicle_name: str = Field(alias="ridercontract__vehicle_type__name")


class DispatchRequestDetail(Schema):
    dispatch_request_id: int
    state: DeliveryState
    cancel_reason: str
    customer: dict
    restaurant: dict
    order: dict
    estimated_delivery_time: str
    estimated_pickup_time: str
    estimated_delivery_distance: str
    estimated_delivery_income: int
    dispatch_request_created_at: str

    class Config:
        use_enum_values = True

    @validator("cancel_reason", pre=True)
    def convert_cancel_reason(cls, reason: str) -> Optional[str]:
        if reason and reason not in (CUSTOMER_ISSUE, RESTAURANT_ISSUE, SYSTEM_ISSUE):
            return CANCEL_REASON_ISSUE_MAP.get(reason, SYSTEM_ISSUE)
        return reason


class RiderStatus(Schema):
    status: str
    current_deliveries: str


class RiderDispatchAcceptanceRate(Schema):
    acceptance_rate: int


class SearchDate(Schema):
    start_at: date = date.today()
    end_at: date = date.today()
