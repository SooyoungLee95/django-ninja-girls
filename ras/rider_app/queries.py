from django.db import transaction

from ras.rideryo.models import RiderAvailability, RiderAvailabilityHistory

from .schemas import RiderAvailability as RiderAvailabilitySchema


def query_update_rider_availability(data: RiderAvailabilitySchema):
    with transaction.atomic():
        availability, _ = RiderAvailability.objects.select_for_update(nowait=True).get_or_create(rider_id=data.rider_id)
        availability.is_available = data.is_available
        availability.save()
        RiderAvailabilityHistory.objects.create(rider=availability, is_available=data.is_available)
    return availability
