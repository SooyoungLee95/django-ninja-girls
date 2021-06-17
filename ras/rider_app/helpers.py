import logging
from http import HTTPStatus

from asgiref.sync import async_to_sync
from django.db.utils import IntegrityError, OperationalError

from ras.common.integration.services.jungleworks.handlers import (
    on_off_duty,
    update_task_status,
)
from ras.rider_app.queries import (
    query_update_rider_availability,
    query_update_rider_dispatch_response,
)

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


def handle_rider_dispatch_updates(data: RiderDispatchResponse, is_jungleworks: bool):
    if is_jungleworks:
        jw_response = async_to_sync(update_task_status)(data)
        return jw_response.relevant_http_status(), jw_response.message
    else:
        try:
            query_update_rider_dispatch_response(data)
            return HTTPStatus.OK, ""
        except IntegrityError as e:
            logger.error(f"[RiderDispatchUpdate] {e!r} {data}")
            return HTTPStatus.BAD_REQUEST, "배차 정보를 확인할 수 없습니다."
        except OperationalError as e:
            logger.error(f"[RiderDispatchUpdate] {e!r} {data}")
            return HTTPStatus.CONFLICT, "상태값을 변경 중입니다."
