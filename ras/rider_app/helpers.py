import logging
import random
from functools import singledispatch
from http import HTTPStatus
from string import digits
from typing import Optional, Union

import jwt
import transitions
from asgiref.sync import async_to_sync
from django.db.utils import DatabaseError, IntegrityError, OperationalError
from django.utils import timezone
from ninja.errors import HttpError
from pydantic import ValidationError

from ras.common.authentication.helpers import decode_token, get_encrypted_payload
from ras.common.integration.services.jungleworks.handlers import (
    on_off_duty,
    retrieve_delivery_task_id,
    update_task_status,
    update_task_status_from_delivery_state,
)
from ras.rider_app.constants import (
    AUTHYO_LOGIN_URL,
    MOCK_DISPATCH_REQUEST_ADDITIONAL_INFO_1,
    MSG_AGREEMENT_NOT_SUBMITTED,
    MSG_INVALID_VALUE,
    MSG_STATE_MACHINE_CANNOT_PROCESS,
    MSG_UNAUTHORIZED,
    RIDER_APP_INITIAL_PASSWORD,
)
from ras.rider_app.enums import PushAction
from ras.rider_app.queries import (
    mock_query_create_dispatch_request_with_task,
    query_create_dispatch_request_with_task,
    query_create_or_replace_rider_service_agreements,
    query_create_rider_delivery_state,
    query_create_rider_dispatch_response,
    query_fcm_token,
    query_get_dispatch_request_states,
    query_get_rider_dispatch_acceptance_rate,
    query_get_rider_profile_summary,
    query_get_rider_service_agreements,
    query_get_rider_working_report,
    query_partial_update_rider_service_agreements,
    query_rider_current_deliveries,
    query_rider_state,
)
from ras.rideryo.enums import DeliveryState, RiderResponse, RiderTransition

from ..common.fcm import FCMSender
from ..rideryo.models import (
    RiderAccount,
    RiderDispatchRequestHistory,
    RiderProfile,
    RiderState,
)
from .schemas import (
    AuthyoPayload,
    DispatchRequestDetail,
    FcmPushPayload,
    MockRiderDispatch,
)
from .schemas import RiderAvailability as RiderAvailabilitySchema
from .schemas import (
    RiderBan,
    RiderDeliveryState,
    RiderDispatch,
    RiderDispatchAcceptanceRate,
    RiderDispatchResponse,
    RiderLoginRequest,
    RiderLoginResponse,
    RiderServiceAgreement,
    RiderServiceAgreementOut,
    RiderServiceAgreementPartial,
    RiderServiceAgreementPartialOut,
    RiderStateOut,
    RiderWorkingReport,
    SearchDate,
    VerificationCodeRequest,
)

logger = logging.getLogger(__name__)


delivery_state_push_action_map = {
    DeliveryState.NEAR_PICKUP: PushAction.NEAR_PICKUP,
    DeliveryState.NEAR_DROPOFF: PushAction.NEAR_DROPOFF,
}


def handle_rider_availability_updates(rider_id, data: RiderAvailabilitySchema, is_jungleworks: bool):
    status, message = HTTPStatus.OK, ""

    if is_jungleworks:
        jw_response = async_to_sync(on_off_duty)(rider_id, data)
        status, message = jw_response.relevant_http_status(), jw_response.message
        if status != HTTPStatus.OK:
            raise HttpError(status, message)

    try:
        rider_state = query_rider_state(rider_id)

        if data.is_available:
            rider_state.start_work()
        else:
            rider_state.end_work()
        return message

    except (RiderState.DoesNotExist, IntegrityError) as e:
        logger.error(f"[RiderAvailability] {e!r} {data}")
        raise HttpError(HTTPStatus.BAD_REQUEST, "라이더를 식별할 수 없습니다.")
    except OperationalError as e:
        logger.error(f"[RiderAvailability] {e!r} {data}")
        raise HttpError(HTTPStatus.CONFLICT, "업무상태를 변경 중입니다.")


def handle_update_task_status(data: RiderDispatchResponse):
    if data.response == RiderResponse.NOTIFIED:
        return HTTPStatus.OK, ""
    jw_response = async_to_sync(update_task_status)(data)
    if jw_response.relevant_http_status() != HTTPStatus.OK:
        raise ValueError(jw_response.message)
    return jw_response.relevant_http_status(), jw_response.message


def handle_rider_dispatch_response(data: RiderDispatchResponse, is_jungleworks: bool):
    try:
        if is_jungleworks:
            handle_update_task_status(data)
        query_create_rider_dispatch_response(data)
    except IntegrityError as e:
        logger.error(f"[RiderDispatchResponse] {e!r} {data}")
        raise HttpError(HTTPStatus.BAD_REQUEST, "유효한 ID 값이 아닙니다.")
    except ValueError as e:
        logger.error(f"[RiderDispatchResponse] {e!r} {data}")
        raise HttpError(HTTPStatus.BAD_REQUEST, str(e))


def handle_rider_dispatch_request_creates(data: RiderDispatch):
    try:
        query_create_dispatch_request_with_task(data=data)
        # TODO: Send FCM push method 호출 - async
    except (RiderProfile.DoesNotExist, DatabaseError) as e:
        logger.error(f"[RiderDispatchRequest] {e!r} {data}")


def send_push_action(rider_id: int, action: PushAction, id: int):
    fcm = FCMSender()
    rider_fcm_token = query_fcm_token(rider_id)
    if not rider_fcm_token:
        return None
    return fcm.send(data=FcmPushPayload(registration_token=rider_fcm_token, action=action, id=id).dict())


def mock_handle_rider_dispatch_request_creates(data: MockRiderDispatch):
    delivery_task_id = handle_retrieve_delivery_task_id(data.pickup_delivery_relationship)
    try:
        dispatch_request = mock_query_create_dispatch_request_with_task(data=data, delivery_task_id=delivery_task_id)
    except (RiderProfile.DoesNotExist, DatabaseError) as e:
        logger.error(f"[RiderDispatchRequest] {e!r} {data}")
    else:
        fixed_rider_id = 626
        response = send_push_action(rider_id=fixed_rider_id, action=PushAction.DISPATCHED, id=dispatch_request.id)
        print(response)


def handle_retrieve_delivery_task_id(pickup_delivery_relationship):
    jw_response = async_to_sync(retrieve_delivery_task_id)(pickup_delivery_relationship)
    if jw_response.relevant_http_status() != HTTPStatus.OK:
        raise ValueError(jw_response.message)
    _, delivery_task = jw_response.data
    return delivery_task["job_id"]


def handle_update_delivery_state(data: RiderDeliveryState):
    if data.state not in (DeliveryState.PICK_UP, DeliveryState.COMPLETED):
        return HTTPStatus.OK, ""

    jw_responses = async_to_sync(update_task_status_from_delivery_state)(data)
    for response in jw_responses:
        if response.relevant_http_status() != HTTPStatus.OK:
            raise ValueError(response.message)
    return jw_responses[0].relevant_http_status(), jw_responses[0].message


def handle_rider_delivery_state(data: RiderDeliveryState, is_jungleworks: bool):
    try:
        if is_jungleworks:
            handle_update_delivery_state(data)
        query_create_rider_delivery_state(data)
    except (IntegrityError, ValueError) as e:
        logger.error(f"[RiderDeliveryState] {e!r} {data}")
        raise HttpError(HTTPStatus.BAD_REQUEST, "배달 상태를 업데이트 할 수 없습니다.")


def mock_delivery_state_push_action(delivery_state: RiderDeliveryState):
    try:
        rider = RiderDispatchRequestHistory.objects.get(pk=delivery_state.dispatch_request_id).rider
    except RiderDispatchRequestHistory.DoesNotExist as e:
        logger.error(f"[DeliveryStatePushAction] {e!r} {delivery_state}")
        return None

    action = delivery_state_push_action_map.get(delivery_state.state)
    if not action:
        return None

    return send_push_action(rider_id=rider.pk, action=action, id=delivery_state.dispatch_request_id)


def handle_rider_ban(data: RiderBan):
    rider_id = data.rider_id
    rider_state = query_rider_state(rider_id)

    if data.is_banned:
        try:
            rider_state = query_rider_state(rider_id)
        except IntegrityError as e:
            logger.error(f"[RiderBan] {e!r} {data}")
            raise HttpError(HTTPStatus.BAD_REQUEST, "라이더를 식별할 수 없습니다.")
        except OperationalError as e:
            logger.error(f"[RiderBan] {e!r} {data}")
            raise HttpError(HTTPStatus.CONFLICT, "업무상태를 변경 중입니다.")
        rider_state.block()
    else:
        rider_state.unblock()

    action = PushAction.BAN if data.is_banned else PushAction.UNDO_BAN
    send_push_action(rider_id=rider_id, action=action, id=rider_id)


def handle_rider_profile_summary(rider_id):
    rider_profile_summary = query_get_rider_profile_summary(rider_id)
    if rider_profile_summary:
        return rider_profile_summary
    else:
        raise HttpError(HTTPStatus.NOT_FOUND, "라이더가 존재하지 않습니다.")


def handle_sns_notification_push_action(topic, message, instance):
    if topic == "order":
        if message.message["event_type"] == "cancelled":
            send_push_action(instance.rider.pk, PushAction.DELIVERY_CANCEL, instance.pk)


def handle_dispatch_request_detail(dispatch_request_ids: list[int]):
    dispatch_requests = query_get_dispatch_request_states(dispatch_request_ids)
    states = [
        DispatchRequestDetail(
            **MOCK_DISPATCH_REQUEST_ADDITIONAL_INFO_1  # TODO: mock data 제거
            | {
                "dispatch_request_id": request.pk,
                "state": request.states[0].delivery_state,
                "cancel_reason": request.cancel_reasons[0].reason if request.cancel_reasons else "",
            }
        )
        for request in dispatch_requests
    ]

    return states


def handle_rider_state(rider_id):
    try:
        rider_state = query_rider_state(rider_id)
    except RiderState.DoesNotExist:
        raise HttpError(HTTPStatus.NOT_FOUND, "")
    current_deliveries = query_rider_current_deliveries(rider_id)
    return RiderStateOut(
        state=rider_state.state,
        current_deliveries=",".join(str(pk) for pk in current_deliveries.values_list("pk", flat=True)),
    )


def handle_rider_dispatch_acceptance_rate(data: SearchDate, rider_id):
    try:
        rider_dispatch_acceptance_rate = query_get_rider_dispatch_acceptance_rate(data, rider_id)
    except IntegrityError as e:
        logger.error(f"[RiderDispatchAcceptanceRate] {e!r} {data}")
        raise HttpError(HTTPStatus.BAD_REQUEST, "유효한 검색 날짜가 아닙니다.")
    else:
        return RiderDispatchAcceptanceRate.parse_obj(rider_dispatch_acceptance_rate or {})


def handle_rider_working_report(data: SearchDate, rider_id):
    rider_working_report = query_get_rider_working_report(data, rider_id)
    return RiderWorkingReport.parse_obj(rider_working_report or {})


def handle_retrieve_rider_service_agreements(rider_id):
    agreements = query_get_rider_service_agreements(rider_id=rider_id)
    try:
        rider_agreements = RiderServiceAgreement(
            **{agreement.get_agreement_type_display(): agreement.agreed for agreement in agreements}
        )
    except ValidationError:
        raise HttpError(HTTPStatus.NOT_FOUND, MSG_AGREEMENT_NOT_SUBMITTED)
    else:
        return rider_agreements


def handle_create_or_replace_rider_service_agreements(
    rider_id, data: RiderServiceAgreement
) -> RiderServiceAgreementOut:
    agreements = query_create_or_replace_rider_service_agreements(rider_id, data)
    return RiderServiceAgreementOut(**data.dict(), agreement_saved_time=timezone.localtime(agreements[-1].modified_at))


def handle_partial_update_rider_service_agreements(
    rider_id, data: RiderServiceAgreementPartial
) -> RiderServiceAgreementPartialOut:
    agreements = query_partial_update_rider_service_agreements(rider_id, data)
    return RiderServiceAgreementPartialOut(
        **data.dict(), agreement_saved_time=timezone.localtime(agreements[-1].modified_at)
    )


def handle_rider_login(email_address, password) -> RiderAccount:
    try:
        rider = RiderAccount.objects.active().get(email_address=email_address)
    except RiderAccount.DoesNotExist:
        raise HttpError(HTTPStatus.BAD_REQUEST, "이메일이 존재하지 않습니다.")

    if not rider.is_valid_password(input_password=password):
        raise HttpError(HTTPStatus.BAD_REQUEST, "패스워드가 일치하지 않습니다.")

    return rider


def check_rider_agreed_required_agreements(rider_id):
    try:
        agreements = handle_retrieve_rider_service_agreements(rider_id=rider_id)
    except HttpError:
        return False
    return agreements.agreed_required()


def handle_rider_authorization(data: RiderLoginRequest) -> RiderLoginResponse:
    rider = handle_rider_login(email_address=data.email_address, password=data.password)
    encrypted_payload = get_encrypted_payload(payload=AuthyoPayload(sub_id=rider.id))
    agreed = check_rider_agreed_required_agreements(rider.pk)

    return RiderLoginResponse(
        authorization_url=f"{AUTHYO_LOGIN_URL}?code={encrypted_payload}",
        password_change_required=data.password == RIDER_APP_INITIAL_PASSWORD,
        checked_service_agreements=agreed,
    )


def handle_rider_action(rider: RiderProfile, action: RiderTransition) -> bool:
    try:
        return getattr(rider.riderstate, action.label)()
    except AttributeError as e:
        logger.error(f"[RiderActions] {rider.pk} {e!r}")
        raise HttpError(HTTPStatus.BAD_REQUEST, MSG_INVALID_VALUE)
    except transitions.MachineError as e:
        logger.error(f"[RiderActions] {rider.pk} {e!r}")
        raise HttpError(HTTPStatus.CONFLICT, MSG_STATE_MACHINE_CANNOT_PROCESS)


def handle_jwt_payload(authorization: str) -> Optional[dict[str, Union[str, int]]]:
    if not authorization:
        return None

    _, token = authorization.split(maxsplit=1)
    try:
        return decode_token(token)
    except jwt.DecodeError:
        raise HttpError(HTTPStatus.UNAUTHORIZED, MSG_UNAUTHORIZED)


def generate_random_verification_code():
    return "".join(random.choices(digits, k=6))


@singledispatch
def get_rider_profile(data):
    raise NotImplementedError("get_rider_profile must be implemented.")


@get_rider_profile.register
def get_rider_profile_by_id(data: int):
    return RiderProfile.objects.filter(rider_id=data).first()


@get_rider_profile.register
def get_rider_profile_by_data(data: VerificationCodeRequest):
    return RiderProfile.objects.filter(rider__email_address=data.email_address, phone_number=data.phone_number).first()
