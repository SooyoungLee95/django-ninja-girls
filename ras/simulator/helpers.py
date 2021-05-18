from ras.common.messaging import SNSMessage, publish_message
from ras.rider.schemas import EventMsgRiderUpdated, RiderState
from ras.simulator.consts import RIDER_UPDATED_TOPIC_ARN
from ras.simulator.schemas import RiderSimulatedAction


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


def get_state_transition(action: RiderSimulatedAction):
    return rider_state_machine[action]
