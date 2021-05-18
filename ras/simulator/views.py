import orjson
from ninja.router import Router

from ras.rider.schemas import EventMsgRiderUpdated, EventType, RiderState
from ras.simulator.schemas import LocationTriggerPayload, RiderStatusTriggerPayload

from .helpers import get_state_of_rider_action, publish_rider_updated

trigger_router = Router()


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


@trigger_router.post("/rider/status", url_name="simulator_rider_status_trigger")
def trigger_rider_status(request, data: RiderStatusTriggerPayload):
    state = get_state_of_rider_action(data.action)
    msg = EventMsgRiderUpdated(
        event_type=EventType.UPDATE,
        event_name=f"rider-{data.action.value}",
        id=data.rider_id,
        zone_id=1,
        current_location=data.location or {"lat": 37.12364, "lng": 127.14424},
        state=state,
    )
    return {
        "message": orjson.loads(msg.json()),
        "response": publish_rider_updated(msg),
    }
