from enum import Enum
from typing import Optional

from ninja.schema import Schema

from ras.rider.schemas import Location


class LocationTriggerPayload(Schema):
    rider_id: int
    location: Location


class RiderSimulatedAction(str, Enum):
    LOGIN = "login"
    LOGOUT = "logout"
    ACCEPT_DELIVERY = "delivery-accepted"
    DECLINE_DELIVERY = "delivery-declined"
    COMPLETE_DELIVERY = "delivery-completed"
    TAKE_A_BREAK = "take-a-break"


class RiderStatusTriggerPayload(Schema):
    rider_id: int
    action: RiderSimulatedAction
    location: Optional[Location]
