from http import HTTPStatus

from ninja.responses import codes_4xx
from ninja.router import Router

from ras.common.integration.services.jungleworks.handlers import (
    should_connect_jungleworks,
)
from ras.common.schemas import ErrorResponse
from ras.rider_app.helpers import (
    handle_rider_availability_updates,
    handle_rider_dispatch_request_creates,
)

from .schemas import RiderAvailability as RiderAvailabilitySchema
from .schemas import RiderDispatch as RiderDispatchResultSchema

rider_router = Router()


@rider_router.put(
    "/availability",
    url_name="rider_app_update_rider_availability",
    summary="업무시작/종료",
    response={200: RiderAvailabilitySchema, codes_4xx: ErrorResponse},
)
def update_rider_availability(request, data: RiderAvailabilitySchema):
    is_jungleworks = should_connect_jungleworks(request)
    status, message = handle_rider_availability_updates(data, is_jungleworks)

    if status != HTTPStatus.OK:
        return status, ErrorResponse(errors=[{"name": "reason", "message": message}])
    return status, data


@rider_router.post(
    "jungleworks/webhook/dispatch_request",
    url_name="rider_app_dispatch_request_webhook",
    summary="라이더 배차 완료 event web hook API",
    response={200: RiderDispatchResultSchema},
)
def dispatch_request_webhook(request, data: RiderDispatchResultSchema):
    handle_rider_dispatch_request_creates(data)
    # TODO: Send FCM push method 호출 - async
    return HTTPStatus.OK, data
