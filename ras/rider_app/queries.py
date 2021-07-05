import logging

from asgiref.sync import sync_to_async
from django.db import transaction

from ras.rideryo.models import (
    DispatchRequestJungleworksTask,
    RiderAvailability,
    RiderAvailabilityHistory,
    RiderDeliveryStateHistory,
    RiderDispatchRequestHistory,
    RiderDispatchResponseHistory,
    RiderFCMToken,
    RiderProfile,
)

from .schemas import MockRiderDispatch as MockRiderDispatchResultSchema
from .schemas import RiderAvailability as RiderAvailabilitySchema
from .schemas import RiderDeliveryState
from .schemas import RiderDispatch as RiderDispatchResultSchema
from .schemas import RiderDispatchResponse as RiderDispatchResponseSchema

logger = logging.getLogger(__name__)


def query_update_rider_availability(rider_id, data: RiderAvailabilitySchema):
    with transaction.atomic():
        availability, _ = RiderAvailability.objects.select_for_update(nowait=True).get_or_create(rider_id=rider_id)
        availability.is_available = data.is_available
        availability.save()
        RiderAvailabilityHistory.objects.create(rider=availability, is_available=data.is_available)
    return availability


def query_create_rider_dispatch_response(data: RiderDispatchResponseSchema):
    return RiderDispatchResponseHistory.objects.create(
        dispatch_request_id=data.dispatch_request_id,
        response=data.response,
    )


def query_create_dispatch_request_with_task(data: RiderDispatchResultSchema):
    rider = RiderProfile.objects.get(pk=data.rider_id)
    with transaction.atomic():
        dispatch_request = RiderDispatchRequestHistory.objects.create(rider=rider, order_id=data.order_id)
        DispatchRequestJungleworksTask.objects.create(
            dispatch_request=dispatch_request,
            pickup_task_id=data.pickup_task_id,
            delivery_task_id=data.delivery_task_id,
        )


def mock_query_create_dispatch_request_with_task(data: MockRiderDispatchResultSchema, delivery_task_id: str):
    rider = RiderProfile.objects.get(jw_fleet_id=data.rider_id)
    with transaction.atomic():
        dispatch_request = RiderDispatchRequestHistory.objects.create(rider=rider, order_id=data.order_id)
        DispatchRequestJungleworksTask.objects.create(
            dispatch_request=dispatch_request,
            pickup_task_id=data.pickup_task_id,
            delivery_task_id=delivery_task_id,
        )
    return dispatch_request


def mock_query_registration_token(rider_id):
    try:
        return RiderFCMToken.objects.get(rider_id=2).registration_token
    except RiderFCMToken.DoesNotExist as e:
        logger.error(f"[RiderFCMToken]: {e!r}")


@sync_to_async
def query_get_dispatch_jungleworks_tasks(dispatch_request_id: int):
    return DispatchRequestJungleworksTask.objects.get(dispatch_request_id=dispatch_request_id)


def query_create_rider_delivery_state(data: RiderDeliveryState):
    return RiderDeliveryStateHistory.objects.create(
        dispatch_request_id=data.dispatch_request_id,
        delivery_state=data.state,
    )
