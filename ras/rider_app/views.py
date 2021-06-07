from http import HTTPStatus

from ninja.router import Router

from ras.common.integration.services.jungleworks.handlers import on_off_duty

from .schemas import RiderAvailability

rider_router = Router()
jungleworks_rider_router = Router()


@rider_router.put(
    "/availability",
    url_name="rider_app_update_rider_availability",
    summary="업무시작/종료",
)
async def update_rider_availability(request, data: RiderAvailability):
    # TODO: update rider state after rider model implementation
    return HTTPStatus.OK, {}


@jungleworks_rider_router.put(  # type: ignore[no-redef]
    "/availability",
    url_name="rider_app_update_rider_availability",
    summary="[JW]업무시작/종료",
)
async def update_rider_availability(request, data: RiderAvailability):  # noqa:F811
    return await on_off_duty(data)
