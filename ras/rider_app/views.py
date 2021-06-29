import json
from http import HTTPStatus
from typing import Callable

from cryptography.fernet import Fernet
from django.contrib.auth.hashers import check_password
from ninja.responses import codes_4xx
from ninja.router import Router

from config.settings.base import FERNET_CRYPTO_KEY
from ras.common.integration.services.jungleworks.handlers import (
    should_connect_jungleworks,
)
from ras.common.schemas import ErrorResponse
from ras.rider_app.helpers import (
    handle_rider_availability_updates,
    handle_rider_dispatch_request_creates,
    handle_rider_dispatch_response,
)

from ..rideryo.models import RiderAccount
from .enums import WebhookName
from .schemas import RiderAvailability as RiderAvailabilitySchema
from .schemas import RiderDispatch as RiderDispatchResultSchema
from .schemas import RiderDispatchResponse as RiderDispatchResponseSchema
from .schemas import RiderLoginRequest, RiderLoginResponse

rider_router = Router()


WEBHOOK_MAP: dict[str, Callable] = {WebhookName.auto_allocation_success: handle_rider_dispatch_request_creates}

RIDER_APP_INITIAL_PASSWORD = "TestTest"


CIPHER = Fernet(key=FERNET_CRYPTO_KEY)


@rider_router.put(
    "/availability",
    url_name="rider_app_update_rider_availability",
    summary="업무시작/종료",
    response={200: RiderAvailabilitySchema, codes_4xx: ErrorResponse},
)
def update_rider_availability(request, data: RiderAvailabilitySchema):
    is_jungleworks = should_connect_jungleworks(request)
    rider_id = 1  # TODO: parse rider id from token
    status, message = handle_rider_availability_updates(rider_id, data, is_jungleworks)

    if status != HTTPStatus.OK:
        return status, ErrorResponse(errors=[{"name": "reason", "message": message}])
    return status, data


@rider_router.post(
    "/dispatch-response",
    url_name="create_rider_dispatch_response",
    summary="배차 확인/수락/거절/무시",
    response={200: RiderDispatchResponseSchema, codes_4xx: ErrorResponse},
)
def create_rider_dispatch_response(request, data: RiderDispatchResponseSchema):
    is_jungleworks = should_connect_jungleworks(request)
    status, message = handle_rider_dispatch_response(data, is_jungleworks)
    if status != HTTPStatus.OK:
        return status, ErrorResponse(errors=[{"name": "reason", "message": message}])
    return status, data


@rider_router.post(
    "jungleworks/webhook/{webhook_type}",
    url_name="rider_app_webhook",
    summary="라이더 web hook API",
    response={200: RiderDispatchResultSchema},
)
def webhook_handler(request, webhook_type: WebhookName, data: RiderDispatchResultSchema):
    WEBHOOK_MAP[webhook_type](data)
    return HTTPStatus.OK, data


@rider_router.post(
    "account/login",
    url_name="rider_app_login",
    summary="라이더 앱 Login API",
    response={200: RiderLoginResponse, 400: None},
)
def login_rider_app(request, data: RiderLoginRequest):
    request_body = data.dict()
    password_change_required = True
    try:
        rider = RiderAccount.objects.get(email_address=request_body["email_address"])
    except RiderAccount.DoesNotExist:
        return HTTPStatus.BAD_REQUEST, None
    if not check_password(request_body["password"], rider.password):
        return HTTPStatus.BAD_REQUEST, None
    payload = {
        "platform": "rideryo-dev",
        "role": "rider",
        "sub_id": "1",
        "base_url": "http://rideryo_base_url",
    }
    token = _generate_encrypted_token(payload)
    if request_body["password"] != RIDER_APP_INITIAL_PASSWORD:
        password_change_required = False
    return HTTPStatus.OK, RiderLoginResponse(
        authorization_url=f"https://staging-authyo.yogiyo.co.kr/api/v1/auth/authorize?code={token}",
        password_change_required=password_change_required,
    )


def _generate_encrypted_token(payload):
    return CIPHER.encrypt(json.dumps(payload).encode("utf-8")).decode("utf-8")
