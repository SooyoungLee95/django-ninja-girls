from http import HTTPStatus

from ninja.responses import codes_4xx
from ninja.router import Router

from ras.common.integration.services.jungleworks.handlers import (
    should_connect_jungleworks,
)
from ras.common.schemas import ErrorResponse
from ras.rider_app.helpers import handle_rider_availability_updates

from ..rideryo.models import (
    JungleWorksTaskHistory,
    RiderDispatchRequestHistory,
    RiderProfile,
)
from .schemas import RiderAvailability as RiderAvailabilitySchema
from .schemas import RiderDispatchResult as RiderDispatchResultSchema

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
    response={200: RiderDispatchResultSchema, codes_4xx: ErrorResponse},
)
def dispatch_request_webhook(request, data: RiderDispatchResultSchema):
    rider = RiderProfile.objects.get(pk=data.rider_id)
    dispatch_request = RiderDispatchRequestHistory.objects.create(rider=rider, order_id=data.order_id)
    JungleWorksTaskHistory.objects.create(
        dispatch_request=dispatch_request, pickup_task_id=data.pickup_task_id, delivery_task_id=data.delivery_task_id
    )

    return HTTPStatus.OK, data
