from datetime import datetime
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
    WAITING_FOR_DELIVERY = "waiting-for-delivery"
    RECEIVE_DELIVERY = "receive-delivery"
    ACCEPT_DELIVERY = "accept-delivery"
    DECLINE_DELIVERY = "decline-delivery"
    DELIVERYING = "deliverying"
    COMPLETE_DELIVERY = "complete-delivery"
    TAKE_A_BREAK = "take-a-break"


class RiderStateTriggerPayload(Schema):
    rider_id: int
    action: RiderSimulatedAction
    location: Optional[Location]


class RiderShiftSimulatedAction(str, Enum):
    SHIFT_START = "shift-start"
    SHIFT_END = "shift-end"


class RiderShiftTriggerPayload(Schema):
    rider_id: int
    start_at: datetime
    end_at: datetime
    action: RiderShiftSimulatedAction
    location: Optional[Location]
