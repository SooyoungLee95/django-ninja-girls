from http import HTTPStatus
from typing import Callable

from ninja import Query
from ninja.errors import HttpError
from ninja.responses import codes_4xx
from ninja.router import Router

from ras.common.integration.services.jungleworks.handlers import (
    should_connect_jungleworks,
)
from ras.common.messaging.schema import SNSMessageForSubscribe
from ras.common.messaging.subscribers import handle_sns_notification
from ras.common.schemas import ErrorResponse
from ras.rider_app.helpers import (
    handle_create_rider_service_agreements,
    handle_dispatch_request_detail,
    handle_partial_update_rider_service_agreements,
    handle_retrieve_rider_service_agreements,
    handle_rider_action,
    handle_rider_authorization,
    handle_rider_availability_updates,
    handle_rider_ban,
    handle_rider_delivery_state,
    handle_rider_dispatch_acceptance_rate,
    handle_rider_dispatch_request_creates,
    handle_rider_dispatch_response,
    handle_rider_profile_summary,
    handle_rider_status,
    handle_rider_working_report,
    handle_sns_notification_push_action,
    mock_delivery_state_push_action,
    mock_handle_rider_dispatch_request_creates,
)
from ras.rideryo.enums import RiderTransition

from ..common.authentication.helpers import extract_jwt_payload
from .constants import MSG_MUST_AGREE_REQUIRED_AGREEMENTS
from .enums import RideryoRole, WebhookName
from .schemas import DispatchRequestDetail
from .schemas import MockRiderDispatch as MockRiderDispatchResultSchema
from .schemas import RiderAvailability as RiderAvailabilitySchema
from .schemas import RiderBan, RiderDeliveryState
from .schemas import RiderDispatch as RiderDispatchResultSchema
from .schemas import RiderDispatchAcceptanceRate
from .schemas import RiderDispatchResponse as RiderDispatchResponseSchema
from .schemas import (
    RiderLoginRequest,
    RiderLoginResponse,
    RiderMypage,
    RiderProfileSummary,
    RiderServiceAgreement,
    RiderServiceAgreementOut,
    RiderServiceAgreementPartial,
    RiderStatus,
    SearchDate,
)

rider_router = Router()
auth_router = Router()
mock_authyo_router = Router()
dispatch_request_router = Router()
sns_router = Router()
action_router = Router()


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
    handle_rider_availability_updates(request.auth.rider_id, data, is_jungleworks)
    return HTTPStatus.OK, data


@rider_router.post(
    "/dispatch-response",
    url_name="create_rider_dispatch_response",
    summary="배차 확인/수락/거절/무시",
    response={200: RiderDispatchResponseSchema, codes_4xx: ErrorResponse},
)
def create_rider_dispatch_response(request, data: RiderDispatchResponseSchema):
    is_jungleworks = should_connect_jungleworks(request)
    handle_rider_dispatch_response(data, is_jungleworks)
    return HTTPStatus.OK, data


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


@rider_router.post(
    "/delivery-state",
    url_name="create_rider_delivery_state",
    summary="배달 상태(픽업완료, 배달완료) 전달",
)
def create_rider_delivery_state(request, data: RiderDeliveryState):
    is_jungleworks = should_connect_jungleworks(request)
    handle_rider_delivery_state(data, is_jungleworks)
    mock_delivery_state_push_action(delivery_state=data)
    return HTTPStatus.OK, data


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
        raise HttpError(HTTPStatus.BAD_REQUEST, "")
    else:
        return HTTPStatus.OK, handle_dispatch_request_detail(req_ids)


@rider_router.put(
    "/ban",
    url_name="rider_app_update_rider_ban",
    summary="업무정지/해제",
    response={200: RiderBan, codes_4xx: ErrorResponse},
    auth=None,
)
def update_rider_ban(request, data: RiderBan):
    payload = extract_jwt_payload(request)
    if payload["role"] != RideryoRole.STAFF:
        raise HttpError(HTTPStatus.FORBIDDEN, "권한이 올바르지 않습니다.")
    handle_rider_ban(data)
    return HTTPStatus.OK, data


@rider_router.get(
    "/profile-summary",
    url_name="retrieve_rider_profile_summary",
    summary="라이더 프로필 정보 조회",
    response={200: RiderProfileSummary, codes_4xx: ErrorResponse},
)
def retrieve_rider_profile_summary(request):
    return HTTPStatus.OK, handle_rider_profile_summary(request.auth.rider_id)


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
    return HTTPStatus.OK, handle_rider_status(rider_id=request.auth.rider_id)


@auth_router.post(
    "login",
    url_name="rider_app_login",
    summary="라이더 앱 Login API",
    response={200: RiderLoginResponse, codes_4xx: ErrorResponse},
    auth=None,
)
def login(request, data: RiderLoginRequest):
    return HTTPStatus.OK, handle_rider_authorization(data)


@rider_router.get(
    "/dispatch-acceptance-rate",
    url_name="retrieve_rider_dispatch_acceptance_rate",
    summary="라이더 배차 수락률 조회",
    response={200: RiderDispatchAcceptanceRate, codes_4xx: ErrorResponse},
)
def retrieve_rider_dispatch_acceptance_rate(request, data: SearchDate = Query(...)):
    return HTTPStatus.OK, handle_rider_dispatch_acceptance_rate(data, rider_id=request.auth.rider_id)


@rider_router.get(
    "/service-agreements",
    url_name="rider_service_agreements",
    summary="라이더 서비스 이용약관 동의여부 조회",
    response={200: RiderServiceAgreement, codes_4xx: ErrorResponse},
)
def retrieve_rider_service_agreements(request):
    return HTTPStatus.OK, handle_retrieve_rider_service_agreements(rider_id=request.auth.pk)


@rider_router.post(
    "/service-agreements",
    url_name="rider_service_agreements",
    summary="라이더 서비스 이용약관 동의여부 저장",
    response={200: RiderServiceAgreementOut, codes_4xx: ErrorResponse},
)
def create_rider_service_agreements(request, data: RiderServiceAgreement):
    if not data.agreed_required():
        raise HttpError(HTTPStatus.BAD_REQUEST, MSG_MUST_AGREE_REQUIRED_AGREEMENTS)
    return HTTPStatus.OK, handle_create_rider_service_agreements(rider_id=request.auth.pk, data=data)


@rider_router.patch(
    "/service-agreements",
    url_name="rider_service_agreements",
    summary="라이더 서비스 이용약관 동의여부 개별저장",
    response={200: RiderServiceAgreementOut, codes_4xx: ErrorResponse},
)
def partial_update_rider_service_agreements(request, data: RiderServiceAgreementPartial):
    return HTTPStatus.OK, handle_partial_update_rider_service_agreements(rider_id=request.auth.pk, data=data)


@auth_router.get("test/jwt/authentication", url_name="test_authentication", summary="JWT 인증 테스트")
def mock_api_for_auth(request):
    return HTTPStatus.OK, {}


@rider_router.get(
    "/mypage",
    url_name="retrieve_rider_mypage",
    summary="라이더 마이페이지",
    response={200: RiderMypage, codes_4xx: ErrorResponse},
)
def retrieve_rider_mypage(request, data: SearchDate = Query(...)):
    return HTTPStatus.OK, {
        **handle_rider_profile_summary(rider_id=request.auth.rider.pk),
        **handle_rider_dispatch_acceptance_rate(data, request.auth.rider.pk),
        **handle_rider_working_report(data, request.auth.rider.pk),
    }


@rider_router.put(
    "actions/{action}",
    url_name="trigger_rider_action",
    summary="라이더 상태 전환 액션",
)
def trigger_rider_action(request, action: RiderTransition):
    return {"success": handle_rider_action(rider=request.auth, action=action)}
