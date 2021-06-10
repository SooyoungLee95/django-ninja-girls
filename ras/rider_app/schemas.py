from ninja.schema import Schema


class RiderAvailability(Schema):
    rider_id: int
    is_available: bool
