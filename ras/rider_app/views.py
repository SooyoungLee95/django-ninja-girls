from http import HTTPStatus
from typing import Callable

from ninja.responses import codes_4xx
from ninja.router import Router

from ras.common.integration.services.jungleworks.handlers import (
    should_connect_jungleworks,
)
from ras.common.schemas import ErrorResponse
from ras.rider_app.helpers import (
    handle_rider_availability_updates,
    handle_rider_delivery_state,
    handle_rider_dispatch_request_creates,
    handle_rider_dispatch_response,
    mock_delivery_state_push_action,
    mock_handle_rider_dispatch_request_creates,
)

from .constants import (
    MOCK_DISPATCH_REQUEST_ADDITIONAL_INFO_1,
    MOCK_DISPATCH_REQUEST_ADDITIONAL_INFO_2,
    MOCK_DISPATCH_REQUEST_ADDITIONAL_INFO_3,
    MOCK_ENCRYPTED_PAYLOAD,
    MOCK_JWT_ACCESS_TOKEN,
    MOCK_JWT_REFRESH_TOKEN,
    MOCK_TOKEN_PUBLISH_URL,
)
from .enums import WebhookName
from .schemas import MockRiderDispatch as MockRiderDispatchResultSchema
from .schemas import RiderAvailability as RiderAvailabilitySchema
from .schemas import RiderDeliveryState
from .schemas import RiderDispatch as RiderDispatchResultSchema
from .schemas import RiderDispatchResponse as RiderDispatchResponseSchema
from .schemas import RiderLoginRequest, RiderLoginResponse

rider_router = Router()
auth_router = Router()
mock_authyo_router = Router()
dispatch_request_router = Router()

WEBHOOK_MAP: dict[str, Callable] = {
    WebhookName.AUTO_ALLOCATION_SUCCESS: handle_rider_dispatch_request_creates,
    WebhookName.MOCK_AUTO_ALLOCATION_SUCCESS: mock_handle_rider_dispatch_request_creates,
}


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
    "jungleworks/mock/webhook/{webhook_type}",
    url_name="mock_rider_app_webhook",
    summary="mock 라이더 web hook API",
)
def mock_webhook_handler(request, webhook_type: WebhookName, data: MockRiderDispatchResultSchema):
    WEBHOOK_MAP[webhook_type](data)
    return HTTPStatus.OK, {}


@auth_router.post(
    "login",
    url_name="rider_app_login",
    summary="라이더 앱 Login API",
    response={200: RiderLoginResponse, codes_4xx: ErrorResponse},
)
def login(request, data: RiderLoginRequest):
    return HTTPStatus.OK, RiderLoginResponse(
        authorization_url=f"{MOCK_TOKEN_PUBLISH_URL}?code={MOCK_ENCRYPTED_PAYLOAD}",
        password_change_required=False,
    )


@mock_authyo_router.get(
    "authorize",
    url_name="mock_token_generate",
    summary="Mock Access, Refresh 토큰 발급",
)
def get_token(request, code: str):
    return HTTPStatus.OK, {"access_token": MOCK_JWT_ACCESS_TOKEN, "refresh_token": MOCK_JWT_REFRESH_TOKEN}


@rider_router.post(
    "/delivery-state",
    url_name="create_rider_delivery_state",
    summary="배달 상태(픽업완료, 배달완료) 전달",
)
def create_rider_delivery_state(request, data: RiderDeliveryState):
    is_jungleworks = should_connect_jungleworks(request)
    status, message = handle_rider_delivery_state(data, is_jungleworks)
    if status != HTTPStatus.OK:
        return status, ErrorResponse(errors=[{"name": "reason", "message": message}])
    mock_delivery_state_push_action(rider_id=1, delivery_state=data)  # NOTE: fixed rider_id
    return status, data


@dispatch_request_router.get(
    "additional-info",
    url_name="mock_rider_app_dispatch_request_additional_info",
    summary="배차 관련 정보(주문, 레스토랑, 고객)",
)
def mock_retrieve_dispatch_requests_additional_info(request, id: str):
    id_list = id.split(",")
    if len(id_list) == 1:
        dispatch_requests_additional_info = MOCK_DISPATCH_REQUEST_ADDITIONAL_INFO_1
    else:
        dispatch_requests_additional_info = {
            "data": [
                MOCK_DISPATCH_REQUEST_ADDITIONAL_INFO_1,
                MOCK_DISPATCH_REQUEST_ADDITIONAL_INFO_2,
                MOCK_DISPATCH_REQUEST_ADDITIONAL_INFO_3,
            ]
        }
    return HTTPStatus.OK, dispatch_requests_additional_info
