import orjson
from ninja.router import Router

from ras.rideryo.schemas import EventMsgRiderUpdated, EventType, RiderState
from ras.simulator.schemas import (
    LocationTriggerPayload,
    RiderShiftTriggerPayload,
    RiderStateTriggerPayload,
)

from .helpers import (
    get_event_type_of_rider_state,
    get_location,
    get_state_of_rider_action,
    get_state_of_shift_action,
    publish_rider_updated,
)

trigger_router = Router(auth=None)


@trigger_router.post("/rider/location", url_name="simulator_rider_location_trigger")
def trigger_rider_location(request, data: LocationTriggerPayload):
    msg = EventMsgRiderUpdated(
        event_type=EventType.UPDATE,
        event_name="rider-location-update",
        id=data.rider_id,
        zone_id=1,
        current_location=data.location,
        state=RiderState.IN_TRANSIT,
    )
    return {
        "message": orjson.loads(msg.json()),
        "response": publish_rider_updated(msg),
    }


@trigger_router.post("/rider/state", url_name="simulator_rider_state_trigger")
def trigger_rider_state(request, data: RiderStateTriggerPayload):
    state = get_state_of_rider_action(data.action)
    event = get_event_type_of_rider_state(state)
    msg = EventMsgRiderUpdated(
        event_type=event,
        event_name=f"rider-{data.action.value}",
        id=data.rider_id,
        zone_id=1,
        current_location=data.location or get_location(),
        state=state,
    )
    return {
        "message": orjson.loads(msg.json()),
        "response": publish_rider_updated(msg),
    }


@trigger_router.post("/rider/shift", url_name="simulator_rider_shift_trigger")
def trigger_rider_shift(request, data: RiderShiftTriggerPayload):
    state = get_state_of_shift_action(data.action)
    event = get_event_type_of_rider_state(state)
    msg = EventMsgRiderUpdated(
        event_type=event,
        event_name=f"rider-{data.action.value}",
        id=data.rider_id,
        zone_id=1,
        current_location=data.location or get_location(),
        state=state,
    )
    return {
        "message": orjson.loads(msg.json()),
        "response": publish_rider_updated(msg),
    }
