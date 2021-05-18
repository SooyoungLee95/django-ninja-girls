from ninja.schema import Schema

from ras.rider.schemas import Location


class LocationTriggerPayload(Schema):
    rider_id: int
    location: Location
