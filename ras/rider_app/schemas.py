import re
from datetime import date, datetime, time, timedelta
from http import HTTPStatus
from typing import Any, Optional

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from ninja.errors import HttpError
from ninja.schema import Field, Schema
from pydantic import root_validator, validator

from ras.rider_app.constants import (
    CANCEL_REASON_ISSUE_MAP,
    CUSTOMER_ISSUE,
    MSG_SUCCESS_CHECKING_VERIFICATION_CODE,
    MSG_SUCCESS_RESET_PASSWORD,
    REGEX_PASSWORD_CONDITION,
    RESTAURANT_ISSUE,
    SYSTEM_ISSUE,
    YOGIYO_CUSTOMER_CENTER_PHONE_NUMBER,
)
from ras.rider_app.enums import PushAction, RideryoRole
from ras.rideryo.enums import DeliveryState
from ras.rideryo.enums import RiderResponse as RiderResponseEnum

MAX_PASSWORD_LENGTH = 8


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
    checked_service_agreements: bool


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


class RiderStateOut(Schema):
    state: str
    current_deliveries: str


class RiderDispatchAcceptanceRate(Schema):
    acceptance_rate: int = 0


class SearchDate(Schema):
    start_at: date = date.today()
    end_at: date = date.today()

    @root_validator
    def check_valid_date(cls, values):
        start_at = values.get("start_at")
        end_at = values.get("end_at")
        if start_at > end_at:
            raise ValueError("검색 시작일이 종료일보다 큽니다.")
        if (end_at - start_at).days > 31:
            raise ValueError("검색 기간은 최대 31일까지 입니다.")
        return values

    def set_start_at_report(self):
        return datetime.combine(self.start_at, time(1, 0, 0))

    def set_end_at_report(self):
        return datetime.combine(self.end_at, time(0, 59, 59)) + timedelta(days=1)


class RiderWorkingReport(Schema):
    total_delivery_count: int = 0
    total_commission: int = 0


class RiderMypage(RiderProfileSummary, RiderDispatchAcceptanceRate, RiderWorkingReport):
    pass


class RiderServiceAgreement(Schema):
    personal_information: bool
    location_based_service: bool
    promotion_receivable: bool = False
    night_promotion_receivable: bool = False

    def agreed_required(self):
        return self.personal_information and self.location_based_service


class RiderServiceAgreementPartial(Schema):
    promotion_receivable: Optional[bool]
    night_promotion_receivable: Optional[bool]

    @root_validator
    def check_requested_agreement(cls, values):
        agreements = values.get("promotion_receivable"), values.get("night_promotion_receivable")
        if all(agmt is None for agmt in agreements):
            raise ValueError("최소 하나의 유효한 이용약관이 포함되어야 합니다.")
        return values


class RiderServiceAgreementOut(Schema):
    agreement_saved_time: str

    @validator("agreement_saved_time", pre=True)
    def validate_agreement_saved_time(cls, value):
        if datetime.strptime(value, "%Y-%m-%d %H:%M:%S"):
            return value


class VerificationCodeRequest(Schema):
    email_address: Optional[str]
    phone_number: str


class SMSMessageData(Schema):
    target: str
    text: str
    sender: str = YOGIYO_CUSTOMER_CENTER_PHONE_NUMBER
    is_lms: bool = False
    lms_subject: str = ""


class SMSMessageInfo(Schema):
    event: str = "send_sms"
    entity: str = "sms"
    tracking_id: str
    msg: dict[str, SMSMessageData]


class CheckVerificationCodeRequest(Schema):
    phone_number: str
    verification_code: str
    token: str


class CheckVerificationCodeResponse(Schema):
    message: str = MSG_SUCCESS_CHECKING_VERIFICATION_CODE
    token: str


class VerificationCodeResponse(Schema):
    token: str


class VerificationInfo(Schema):
    rider_id: int
    phone_number: Optional[str]
    verification_code: Optional[str]


class ResetPasswordRequest(Schema):
    new_password: str
    token: str

    @validator("new_password")
    def check_new_password(cls, v):
        if not re.match(REGEX_PASSWORD_CONDITION, v):
            raise HttpError(HTTPStatus.BAD_REQUEST, "패스워드 형식이 일치하지 않습니다.")
        return v


class ResetPasswordResponse(Schema):
    message: str = MSG_SUCCESS_RESET_PASSWORD
