from http import HTTPStatus
from typing import Callable, Union

import jwt
from django.conf import settings
from ninja import Query
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
    handle_rider_dispatch_acceptance_rate,
    handle_rider_dispatch_request_creates,
    handle_rider_dispatch_response,
    handle_rider_profile_summary,
    handle_rider_status,
    handle_sns_notification_push_action,
    mock_delivery_state_push_action,
    mock_handle_rider_dispatch_request_creates,
)

from ..common.authentication.helpers import AuthyoTokenAuthenticator
from ..rideryo.models import RiderAccount
from .constants import (
    AUTHYO_LOGIN_URL,
    MOCK_JWT_ACCESS_TOKEN,
    MOCK_JWT_REFRESH_TOKEN,
    RIDER_APP_INITIAL_PASSWORD,
)
from .enums import WebhookName
from .schemas import AuthyoPayload, DispatchRequestDetail
from .schemas import MockRiderDispatch as MockRiderDispatchResultSchema
from .schemas import RiderAvailability as RiderAvailabilitySchema
from .schemas import RiderBan, RiderDeliveryState
from .schemas import RiderDispatch as RiderDispatchResultSchema
from .schemas import RiderDispatchAcceptanceRate
from .schemas import RiderDispatchResponse as RiderDispatchResponseSchema
from .schemas import (
    RiderLoginRequest,
    RiderLoginResponse,
    RiderProfileSummary,
    RiderStatus,
    SearchDate,
)

rider_router = Router()
auth_router = Router()
mock_authyo_router = Router()
dispatch_request_router = Router()
sns_router = Router()


WEBHOOK_MAP: dict[str, Callable] = {
    WebhookName.AUTO_ALLOCATION_SUCCESS: handle_rider_dispatch_request_creates,
    WebhookName.MOCK_AUTO_ALLOCATION_SUCCESS: mock_handle_rider_dispatch_request_creates,
}

token_authenticator = AuthyoTokenAuthenticator()


def _extract_jwt_payload(request) -> dict[str, Union[str, int]]:
    _, token = request.headers["Authorization"].split()
    payload = jwt.decode(jwt=token, key=settings.AUTHYO.SECRET_KEY, algorithms=[settings.AUTHYO.ALGORITHM])
    return payload


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
    auth=None,
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
    url_name="mock_rider_app_dispatch_requests_detail",
    summary="배차 관련 정보 (상태, 주문, 레스토랑, 고객)",
    response={200: list[DispatchRequestDetail], codes_4xx: ErrorResponse},
)
def retrieve_dispatch_requests_detail(request, id: str):
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


@rider_router.get(
    "/status",
    url_name="rider_app_rider_status",
    summary="라이더 상태 조회",
    response={200: RiderStatus, codes_4xx: ErrorResponse},
)
def retrieve_rider_status(request):
    payload = _extract_jwt_payload(request)
    return handle_rider_status(rider_id=payload["sub_id"])


@auth_router.post(
    "login",
    url_name="rider_app_login",
    summary="라이더 앱 Login API",
    response={200: RiderLoginResponse, codes_4xx: ErrorResponse},
    auth=None,
)
def login(request, data: RiderLoginRequest):
    request_body = data.dict()
    try:
        rider = RiderAccount.objects.active().get(email_address=request_body["email_address"])
    except RiderAccount.DoesNotExist:
        return HTTPStatus.BAD_REQUEST, ErrorResponse(message="이메일이 존재하지 않습니다.")

    if not rider.is_valid_password(input_password=request_body["password"]):
        return HTTPStatus.BAD_REQUEST, ErrorResponse(message="패스워드가 일치하지 않습니다.")

    encrypted_payload = token_authenticator.get_encrypted_payload(payload=AuthyoPayload(sub_id=rider.id))

    return HTTPStatus.OK, RiderLoginResponse(
        authorization_url=f"{AUTHYO_LOGIN_URL}?code={encrypted_payload}",
        password_change_required=request_body["password"] == RIDER_APP_INITIAL_PASSWORD,
    )


@rider_router.get(
    "/dispatch-acceptance-rate",
    url_name="retrieve_rider_dispatch_acceptance_rate",
    summary="라이더 배차 수락률 조회",
    response={200: RiderDispatchAcceptanceRate, codes_4xx: ErrorResponse},
)
def retrieve_rider_dispatch_acceptance_rate(request, data: SearchDate = Query(...)):
    # TODO: parse rider id from token
    status, message = handle_rider_dispatch_acceptance_rate(data.rider_id, data)
    if status != HTTPStatus.OK:
        return status, ErrorResponse(message=message)
    return status, message


@auth_router.get("test/jwt/authentication", url_name="test_authentication", summary="JWT 인증 테스트")
def mock_api_for_auth(request):
    return HTTPStatus.OK, {}
