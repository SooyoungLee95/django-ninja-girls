from ras.common.messaging import SNSMessage, publish_message
from ras.rider.schemas import EventMsgRiderUpdated
from ras.simulator.consts import RIDER_UPDATED_TOPIC_ARN


def publish_rider_updated(event_msg: EventMsgRiderUpdated):
    sns_message = SNSMessage(topic_arn=RIDER_UPDATED_TOPIC_ARN, message=event_msg.json())
    return publish_message(sns_message)
