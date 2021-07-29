import datetime
import logging
from functools import singledispatch

from asgiref.sync import sync_to_async
from django.db import transaction
from django.db.models import Case, Count, F, FloatField, Sum, When
from django.db.models.functions import Coalesce, Round
from django.db.models.query import Prefetch

from ras.common.messaging.consts import RIDER_WORKING_STATE
from ras.common.messaging.helpers import trigger_event
from ras.rideryo.enums import DeliveryState
from ras.rideryo.models import (
    DispatchRequestJungleworksTask,
    RiderAvailability,
    RiderAvailabilityHistory,
    RiderDeliveryCancelReason,
    RiderDeliveryStateHistory,
    RiderDispatchRequestHistory,
    RiderDispatchResponseHistory,
    RiderFCMToken,
    RiderProfile,
)

from ..rideryo.enums import RiderResponse
from .schemas import MockRiderDispatch as MockRiderDispatchResultSchema
from .schemas import RiderAvailability as RiderAvailabilitySchema
from .schemas import RiderDeliveryState
from .schemas import RiderDispatch as RiderDispatchResultSchema
from .schemas import RiderDispatchResponse as RiderDispatchResponseSchema
from .schemas import SearchDate

logger = logging.getLogger(__name__)

RIDER_RESPONSE_DELIVERY_STATE_MAP = {
    RiderResponse.NOTIFIED: DeliveryState.NOTIFIED,
    RiderResponse.ACCEPTED: DeliveryState.ACCEPTED,
    RiderResponse.DECLINED: DeliveryState.DECLINED,
    RiderResponse.IGNORED: DeliveryState.IGNORED,
}


@singledispatch
@trigger_event(RIDER_WORKING_STATE)
def query_update_rider_availability(data: RiderAvailabilitySchema, rider_id) -> RiderAvailability:
    with transaction.atomic():
        availability, _ = RiderAvailability.objects.select_for_update(nowait=True).get_or_create(rider_id=rider_id)
        availability.is_available = data.is_available
        availability.save()
        RiderAvailabilityHistory.objects.create(rider=availability, is_available=data.is_available)
    return availability


@query_update_rider_availability.register
@trigger_event(RIDER_WORKING_STATE)
def _(data: bool, rider_id) -> RiderAvailability:
    with transaction.atomic():
        availability, _ = RiderAvailability.objects.select_for_update(nowait=True).get_or_create(rider_id=rider_id)
        availability.is_available = data
        availability.save()
        RiderAvailabilityHistory.objects.create(rider=availability, is_available=data)
    return availability


def query_create_rider_dispatch_response(data: RiderDispatchResponseSchema):
    with transaction.atomic():
        RiderDeliveryStateHistory.objects.create(
            dispatch_request_id=data.dispatch_request_id,
            delivery_state=RIDER_RESPONSE_DELIVERY_STATE_MAP[data.response],
        )
        return RiderDispatchResponseHistory.objects.create(
            dispatch_request_id=data.dispatch_request_id,
            response=data.response,
        )


def query_create_dispatch_request_with_task(data: RiderDispatchResultSchema):
    rider = RiderProfile.objects.get(pk=data.rider_id)
    with transaction.atomic():
        dispatch_request = RiderDispatchRequestHistory.objects.create(rider=rider, order_id=data.order_id)
        RiderDeliveryStateHistory.objects.create(
            dispatch_request=dispatch_request, delivery_state=DeliveryState.DISPATCHED
        )
        DispatchRequestJungleworksTask.objects.create(
            dispatch_request=dispatch_request,
            pickup_task_id=data.pickup_task_id,
            delivery_task_id=data.delivery_task_id,
        )


def mock_query_create_dispatch_request_with_task(data: MockRiderDispatchResultSchema, delivery_task_id: str):
    rider = RiderProfile.objects.get(jw_fleet_id=data.rider_id)
    with transaction.atomic():
        dispatch_request = RiderDispatchRequestHistory.objects.create(rider=rider, order_id=data.order_id)
        RiderDeliveryStateHistory.objects.create(
            dispatch_request=dispatch_request, delivery_state=DeliveryState.DISPATCHED
        )
        DispatchRequestJungleworksTask.objects.create(
            dispatch_request=dispatch_request,
            pickup_task_id=data.pickup_task_id,
            delivery_task_id=delivery_task_id,
        )
    return dispatch_request


def query_fcm_token(rider_id):
    try:
        return RiderFCMToken.objects.get(rider_id=rider_id).registration_token
    except RiderFCMToken.DoesNotExist as e:
        logger.error(f"[RiderFCMToken] {e!r}")


@sync_to_async
def query_get_dispatch_jungleworks_tasks(dispatch_request_id: int):
    return DispatchRequestJungleworksTask.objects.get(dispatch_request_id=dispatch_request_id)


def query_create_rider_delivery_state(data: RiderDeliveryState):
    return RiderDeliveryStateHistory.objects.create(
        dispatch_request_id=data.dispatch_request_id,
        delivery_state=data.state,
    )


def query_get_rider_profile_summary(rider_id):
    return (
        RiderProfile.objects.filter(rider=rider_id)
        .annotate(vehicle_name=F("ridercontract__vehicle_type__name"))
        .values("full_name", "ridercontract__contract_type", "ridercontract__vehicle_type__name")
        .first()
    )


def query_get_dispatch_request_states(dispatch_request_ids: list[int]):
    latest_cancel_reason_qs = RiderDeliveryCancelReason.objects.order_by("-created_at")
    latest_state_qs = RiderDeliveryStateHistory.objects.order_by("-created_at")
    return (
        RiderDispatchRequestHistory.objects.prefetch_related(
            Prefetch(
                "riderdeliverycancelreason_set",
                queryset=latest_cancel_reason_qs,
                to_attr="cancel_reasons",
            )
        )
        .prefetch_related(
            Prefetch(
                "riderdeliverystatehistory_set",
                queryset=latest_state_qs,
                to_attr="states",
            )
        )
        .filter(id__in=dispatch_request_ids)
    )


def query_rider_status(rider_id):
    # TODO: update after rider state machine implementation
    return RiderAvailability.objects.get(pk=rider_id)


def query_rider_current_deliveries(rider_id):
    return RiderDispatchRequestHistory.objects.filter(rider_id=rider_id).exclude(
        riderdeliverystatehistory__delivery_state__in=(
            DeliveryState.DECLINED,
            DeliveryState.IGNORED,
            DeliveryState.COMPLETED,
            DeliveryState.CANCELLED,
        )
    )


def query_get_rider_dispatch_acceptance_rate(data: SearchDate, rider_id):
    start_at = datetime.datetime.combine(data.start_at, datetime.time(1, 0, 0))
    end_at = datetime.datetime.combine(data.end_at, datetime.time(0, 59, 59)) + datetime.timedelta(days=1)
    return (
        RiderDispatchResponseHistory.objects.filter(
            dispatch_request__rider__rider_id=rider_id, created_at__range=[start_at, end_at]
        )
        .values("dispatch_request__rider__rider_id")
        .annotate(
            acceptance_rate=Round(
                (
                    Sum(Case(When(response=RiderResponse.ACCEPTED, then=1), default=0, output_field=FloatField()))
                    / Count("dispatch_request__rider__rider_id")
                )
                * 100
            )
        )
        .values("acceptance_rate")
        .order_by("dispatch_request__rider__rider_id")
        .first()
    )


def query_get_rider_working_report(data: SearchDate, rider_id):
    return (
        RiderDispatchResponseHistory.objects.select_related("dispatch_request__riderpaymenthistory_set")
        .filter(
            dispatch_request__rider__rider_id=rider_id,
            created_at__range=[data.set_start_at_report(), data.set_end_at_report()],
            response=RiderResponse.ACCEPTED,
        )
        .values("dispatch_request__rider__rider_id")
        .annotate(
            total_delivery_count=Count("id", distinct=True),
            total_commission=Coalesce(Sum("dispatch_request__riderpaymenthistory__delivery_commission__fee"), 0),
        )
        .values("total_delivery_count", "total_commission")
        .order_by("dispatch_request__rider__rider_id")
        .first()
    )
