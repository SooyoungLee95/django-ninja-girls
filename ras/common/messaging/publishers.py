from __future__ import annotations

import logging
from functools import singledispatch
from typing import TYPE_CHECKING

from botocore.exceptions import BotoCoreError

from ras.common.messaging.connections import sns_client
from ras.common.messaging.consts import RIDER_WORKING_STATE
from ras.common.messaging.schema import SNSMessageForPublish
from ras.rideryo.enums import RiderState as RiderStateEnum
from ras.rideryo.schemas import EventMsgRiderWorkingState

if TYPE_CHECKING:
    from ras.rideryo.models import RiderState


logger = logging.getLogger(__name__)
event_cls_to_type = {RIDER_WORKING_STATE: EventMsgRiderWorkingState}


@singledispatch
def publish_event(instance, event_type):
    raise NotImplementedError("publish_event must be implemented.")


def publish_rider_working_state(instance: RiderState):
    event_msg_cls = event_cls_to_type[RIDER_WORKING_STATE]
    event_msg = event_msg_cls(
        rider_id=instance.rider.pk,
        state="available" if instance.state == RiderStateEnum.READY else "unavailable",
    )
    sns_message = SNSMessageForPublish(topic_arn=event_msg._arn, message=event_msg.json(exclude={"_arn"}))
    return publish_message(sns_message)


def publish_message(sns_message: SNSMessageForPublish):
    try:
        return sns_client.publish(**sns_message.dict(exclude_none=True, exclude_unset=True))
    except BotoCoreError as e:
        logger.critical(f"[SNS] publish error {e!r}")
        return None
