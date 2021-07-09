import pytest

from ras.rideryo.schemas import EventMsg, EventMsgRiderWorkingState


@pytest.mark.parametrize(
    "event_msg_cls, extra_body",
    [
        (EventMsgRiderWorkingState, {"event_type": "working-state", "rider_id": "1", "state": "available"}),
    ],
)
def test_event_msg_schema(event_msg_cls, extra_body):
    # When: 이벤트 type, name 정보가 있고, EventMsg 객체를 생성하면,
    data = {"_arn": "rider:000000"}
    event_msg = event_msg_cls(**data, **extra_body)

    # Then: EventMsg 객체가 생성된다.
    assert event_msg is not None
    assert isinstance(event_msg, event_msg_cls)
    assert issubclass(type(event_msg), EventMsg)
