import logging
from http import HTTPStatus

from django.db.utils import IntegrityError, OperationalError

from ras.common.integration.services.jungleworks.handlers import on_off_duty
from ras.rider_app.queries import query_update_rider_availability

from .schemas import RiderAvailability as RiderAvailabilitySchema

logger = logging.getLogger(__name__)


async def handle_rider_availability_updates(data: RiderAvailabilitySchema, jungleworks: bool):
    if jungleworks:
        jw_response = await on_off_duty(data)
        return jw_response.relevant_http_status(), jw_response.message
    else:
        try:
            await query_update_rider_availability(data)  # type: ignore[misc,arg-type]
            return HTTPStatus.OK, ""
        except IntegrityError as e:
            logger.error(f"[RiderAvailability] {e!r} {data}")
            return HTTPStatus.BAD_REQUEST, "라이더를 식별할 수 없습니다."
        except OperationalError as e:
            logger.error(f"[RiderAvailability] {e!r} {data}")
            return HTTPStatus.CONFLICT, "업무상태를 변경 중입니다."
