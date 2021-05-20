from ras.common.messaging import SNSMessage, publish_message
from ras.rider.schemas import EventMsgRiderUpdated, EventType, RiderState
from ras.simulator.consts import RIDER_UPDATED_TOPIC_ARN
from ras.simulator.schemas import RiderShiftSimulatedAction, RiderSimulatedAction


def publish_rider_updated(event_msg: EventMsgRiderUpdated):
    sns_message = SNSMessage(topic_arn=RIDER_UPDATED_TOPIC_ARN, message=event_msg.json())
    return publish_message(sns_message)


rider_state_machine = {
    RiderSimulatedAction.LOGIN: RiderState.AVAILABLE,
    RiderSimulatedAction.LOGOUT: RiderState.NOT_WORKING,
    RiderSimulatedAction.ACCEPT_DELIVERY: RiderState.IN_TRANSIT,
    RiderSimulatedAction.DECLINE_DELIVERY: RiderState.AVAILABLE,
    RiderSimulatedAction.COMPLETE_DELIVERY: RiderState.AVAILABLE,
    RiderSimulatedAction.TAKE_A_BREAK: RiderState.BREAK,
}


rider_shift_state_machine = {
    RiderShiftSimulatedAction.SHIFT_START: RiderState.AVAILABLE,
    RiderShiftSimulatedAction.SHIFT_END: RiderState.NOT_WORKING,
}

rider_state_event_type_mapping = {
    RiderState.AVAILABLE: EventType.ADD,
    RiderState.IN_TRANSIT: EventType.UPDATE,
    RiderState.BREAK: EventType.DELETE,
    RiderState.NOT_WORKING: EventType.DELETE,
}


def get_state_of_rider_action(action: RiderSimulatedAction):
    return rider_state_machine[action]


def get_state_of_shift_action(action: RiderShiftSimulatedAction):
    return rider_shift_state_machine[action]


def get_event_type_of_rider_state(state: RiderState):
    return rider_state_event_type_mapping[state]
