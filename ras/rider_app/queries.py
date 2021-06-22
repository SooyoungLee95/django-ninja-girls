from django.db import transaction

from ras.rideryo.models import (
    DispatchRequestJungleworksTask,
    RiderAvailability,
    RiderAvailabilityHistory,
    RiderDispatchRequestHistory,
    RiderDispatchResponseHistory,
    RiderProfile,
)

from .schemas import RiderAvailability as RiderAvailabilitySchema
from .schemas import RiderDispatch as RiderDispatchResultSchema
from .schemas import RiderDispatchResponse as RiderDispatchResponseSchema


def query_update_rider_availability(data: RiderAvailabilitySchema):
    with transaction.atomic():
        availability, _ = RiderAvailability.objects.select_for_update(nowait=True).get_or_create(rider_id=data.rider_id)
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
