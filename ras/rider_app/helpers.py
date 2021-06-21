import logging
from http import HTTPStatus

from asgiref.sync import async_to_sync
from django.db.utils import IntegrityError, OperationalError

from ras.common.integration.services.jungleworks.handlers import (
    on_off_duty,
    update_task_status,
)
from ras.rider_app.queries import (
    query_create_rider_dispatch_response,
    query_update_rider_availability,
)
from ras.rideryo.enums import RiderResponse

from .schemas import RiderAvailability as RiderAvailabilitySchema
from .schemas import RiderDispatchResponse

logger = logging.getLogger(__name__)


def handle_rider_availability_updates(data: RiderAvailabilitySchema, is_jungleworks: bool):
    if is_jungleworks:
        jw_response = async_to_sync(on_off_duty)(data)
        return jw_response.relevant_http_status(), jw_response.message
    else:
        try:
            query_update_rider_availability(data)
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
