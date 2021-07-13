import logging
from http import HTTPStatus

from asgiref.sync import async_to_sync
from django.db.utils import DatabaseError, IntegrityError, OperationalError

from ras.common.integration.services.jungleworks.handlers import (
    on_off_duty,
    retrieve_delivery_task_id,
    update_task_status,
    update_task_status_from_delivery_state,
)
from ras.rider_app.enums import PushAction
from ras.rider_app.queries import (
    mock_query_create_dispatch_request_with_task,
    query_create_dispatch_request_with_task,
    query_create_rider_delivery_state,
    query_create_rider_dispatch_response,
    query_fcm_token,
    query_get_rider_profile_summary,
    query_update_rider_availability,
)
from ras.rideryo.enums import DeliveryState, RiderResponse

from ..common.fcm import FCMSender
from ..rideryo.models import RiderDispatchRequestHistory, RiderProfile
from .schemas import FcmPushPayload, MockRiderDispatch
from .schemas import RiderAvailability as RiderAvailabilitySchema
from .schemas import RiderDeliveryState, RiderDispatch, RiderDispatchResponse

logger = logging.getLogger(__name__)


delivery_state_push_action_map = {
    DeliveryState.NEAR_PICKUP: PushAction.NEAR_PICKUP,
    DeliveryState.NEAR_DROPOFF: PushAction.NEAR_DROPOFF,
}


def handle_rider_availability_updates(rider_id, data: RiderAvailabilitySchema, is_jungleworks: bool):
    if is_jungleworks:
        jw_response = async_to_sync(on_off_duty)(rider_id, data)
        return jw_response.relevant_http_status(), jw_response.message
    else:
        try:
            query_update_rider_availability(rider_id, data)
            return HTTPStatus.OK, ""
        except IntegrityError as e:
            logger.error(f"[RiderAvailability] {e!r} {data}")
            return HTTPStatus.BAD_REQUEST, "라이더를 식별할 수 없습니다."
        except OperationalError as e:
            logger.error(f"[RiderAvailability] {e!r} {data}")
            return HTTPStatus.CONFLICT, "업무상태를 변경 중입니다."


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
        return HTTPStatus.BAD_REQUEST, "유효한 ID 값이 아닙니다."
    except ValueError as e:
        logger.error(f"[RiderDispatchResponse] {e!r} {data}")
        return HTTPStatus.BAD_REQUEST, str(e)
    else:
        return HTTPStatus.OK, ""


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
    response = fcm.send(data=FcmPushPayload(registration_token=rider_fcm_token, action=action, id=id).dict())
    return response


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
        return HTTPStatus.BAD_REQUEST, "배달 상태를 업데이트 할 수 없습니다."
    else:
        return HTTPStatus.OK, ""


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


def handle_rider_profile_summary(rider_id):
    try:
        rider_profile = query_get_rider_profile_summary(rider_id)
    except RiderProfile.DoesNotExist as e:
        logger.error(f"[RiderProfile] {e!r} {rider_id}")
        return HTTPStatus.BAD_REQUEST, "라이더가 존재하지 않습니다."
    else:
        return HTTPStatus.OK, rider_profile
