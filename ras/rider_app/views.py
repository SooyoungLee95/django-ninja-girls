from http import HTTPStatus
from typing import Callable

from ninja.responses import codes_4xx
from ninja.router import Router

from ras.common.integration.services.jungleworks.handlers import (
    should_connect_jungleworks,
)
from ras.common.messaging.helpers import handle_sns_notification
from ras.common.messaging.schema import SNSMessageForSubscribe
from ras.common.schemas import ErrorResponse
from ras.rider_app.helpers import (
    handle_dispatch_request_detail,
    handle_rider_availability_updates,
    handle_rider_ban,
    handle_rider_delivery_state,
    handle_rider_dispatch_request_creates,
    handle_rider_dispatch_response,
    handle_rider_profile_summary,
    handle_sns_notification_push_action,
    mock_delivery_state_push_action,
    mock_handle_rider_dispatch_request_creates,
)

from .constants import (
    MOCK_ENCRYPTED_PAYLOAD,
    MOCK_JWT_ACCESS_TOKEN,
    MOCK_JWT_REFRESH_TOKEN,
    MOCK_TOKEN_PUBLISH_URL,
)
from .enums import WebhookName
from .schemas import DispatchRequestDetail
from .schemas import MockRiderDispatch as MockRiderDispatchResultSchema
from .schemas import RiderAvailability as RiderAvailabilitySchema
from .schemas import RiderBan, RiderDeliveryState
from .schemas import RiderDispatch as RiderDispatchResultSchema
from .schemas import RiderDispatchResponse as RiderDispatchResponseSchema
from .schemas import RiderLoginRequest, RiderLoginResponse, RiderProfileSummary

rider_router = Router()
auth_router = Router()
mock_authyo_router = Router()
dispatch_request_router = Router()
sns_router = Router()


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
    rider_id = 1049903  # TODO: parse rider id from token
    status, message = handle_rider_availability_updates(rider_id, data, is_jungleworks)

    if status != HTTPStatus.OK:
        return status, ErrorResponse(message=message)
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
        return status, ErrorResponse(message=message)
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
        return status, ErrorResponse(message=message)
    mock_delivery_state_push_action(delivery_state=data)
    return status, data


@dispatch_request_router.get(
    "/",
    url_name="mock_rider_app_dispatch_requests",
    summary="배차 관련 정보 (상태, 주문, 레스토랑, 고객)",
    response={200: list[DispatchRequestDetail], codes_4xx: ErrorResponse},
)
def retrieve_dispatch_requests_status(request, id: str):
    try:
        req_ids = [int(req_id) for req_id in id.split(",")]
    except ValueError:
        return HTTPStatus.BAD_REQUEST, ErrorResponse()
    else:
        return handle_dispatch_request_detail(req_ids)


@rider_router.put(
    "/ban",
    url_name="rider_app_update_rider_ban",
    summary="업무정지/해제",
    response={200: RiderBan, codes_4xx: ErrorResponse},
)
def update_rider_ban(request, data: RiderBan):
    # TODO: requires permission check! Admin only!
    status, message = handle_rider_ban(data)
    if status != HTTPStatus.OK:
        return status, ErrorResponse(message=message)
    return status, data


@rider_router.get(
    "/profile-summary",
    url_name="retrieve_rider_profile_summary",
    summary="라이더 프로필 정보 조회",
    response={200: RiderProfileSummary, codes_4xx: ErrorResponse},
)
def retrieve_rider_profile_summary(request, rider_id):
    # TODO: parse rider id from token
    status, message = handle_rider_profile_summary(rider_id)
    if status != HTTPStatus.OK:
        return status, ErrorResponse(message=message)
    return status, message


@sns_router.post(
    "/subs/{topic}",
    url_name="rider_app_sns_notification",
    summary="SNS 이벤트 처리",
)
def subscribe_sns_event(request, topic):
    body = request.body.decode()
    message = SNSMessageForSubscribe.parse_raw(body)
    message_type = request.headers.get("x-amz-sns-message-type")
    instance = handle_sns_notification(message_type, message)
    handle_sns_notification_push_action(topic, message, instance)
    return HTTPStatus.OK
