from uuid import UUID

import pytest

from ras.rider.schemas import EventMsg, EventType


@pytest.mark.parametrize(
    "expected_result, event_id",
    [
        (True, "ras:8db523c0-0e69-42cf-afdb-673bdf6f99d6"),
        (False, "das:8db523c0-0e69-42cf-afdb-673bdf6f99d6"),
        (False, "ras:8db523c0"),
        (False, "8db523c0-0e69-42cf-afdb-673bdf6f99d6"),
    ],
)
def test_event_msg_schema_event_id_validator(expected_result, event_id):
    # Given: 이벤트ID와 예상검증결과가 주어진 경우
    # When: 이벤트ID 검증로직 실행 시
    validator_result = False
    try:
        EventMsg.check_event_id(event_id)
        validator_result = True
    except (TypeError, ValueError):
        pass
    finally:
        # Then: 예샹한 검증결과와 일치한다.
        assert validator_result is expected_result


def test_event_msg_schema():
    # When: 이벤트 type, name 정보가 있고, EventMsg 객체를 생성하면,
    expected_event_type = "add"
    expected_event_name = "test-event"
    data = {"event_type": expected_event_type, "event_name": expected_event_name}
    event_msg = EventMsg(**data)

    # Then: EventMsg 객체가 생성된다.
    assert event_msg is not None
    assert isinstance(event_msg, EventMsg)

    # And: 유효한 event_id가 자동생성되고,
    assert isinstance(event_msg.event_id, str)
    service, _, uuid = event_msg.event_id.partition(":")
    assert service == "ras"
    try:
        UUID(uuid)
    except ValueError:
        pytest.fail("event_id must be an UUID type.")

    # And: type과 name이 올바르게 설정된다.
    assert isinstance(event_msg.event_type, EventType)
    assert event_msg.event_type.value == expected_event_type
    assert event_msg.event_name == expected_event_name
