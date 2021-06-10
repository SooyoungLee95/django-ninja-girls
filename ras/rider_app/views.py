from http import HTTPStatus

from ninja.router import Router

from ras.common.integration.services.jungleworks.handlers import (
    on_off_duty,
    should_connect_jungleworks,
)
from ras.common.schemas import ErrorResponse

from .schemas import RiderAvailability

rider_router = Router()


@rider_router.put(
    "/availability",
    url_name="rider_app_update_rider_availability",
    summary="업무시작/종료",
    response={200: RiderAvailability, 400: ErrorResponse},
)
async def update_rider_availability(request, data: RiderAvailability):
    if should_connect_jungleworks(request):
        jw_response = await on_off_duty(data)
        status = jw_response.relevant_http_status()
        message = jw_response.message
    else:
        # TODO: update rider state after rider model implementation
        status = HTTPStatus.OK
        message = ""

    if status != HTTPStatus.OK:
        return status, ErrorResponse(errors=[{"name": "reason", "message": message}])

    return status, data
