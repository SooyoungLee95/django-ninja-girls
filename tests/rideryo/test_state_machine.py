from unittest.mock import Mock, patch

import pytest

from ras.rideryo.enums import RiderState, RiderTransition


@pytest.mark.django_db(transaction=True)
def test_start_work_ondemand_should_auto_update_to_ready_state(rider_state):
    # Given: AVAILABLE 상태일 때,
    rider_state.state = RiderState.AVAILABLE
    # TODO: And: 온디멘드 조건일 때,

    # When: 근무 시작 시,
    rider_state.start_work()

    # Then: READY 상태로 전환된다
    rider_state.refresh_from_db()
    assert rider_state.state == RiderState.READY


@pytest.mark.django_db(transaction=True)
def test_start_work_ondemand_should_call_start_dispatch(rider_state):
    # Given: AVAILABLE 상태일 때,
    rider_state.state = RiderState.AVAILABLE
    # TODO: And: 온디멘드 조건일 때,

    # When: 근무 시작 시,
    mock_start_dispatch = Mock()

    # Then: enable_new_dispatch 트리거가 실행된다
    with patch.object(rider_state, RiderTransition.ENABLE_NEW_DISPATCH.value, mock_start_dispatch):
        rider_state.start_work()
        mock_start_dispatch.assert_called_once()


@pytest.mark.django_db(transaction=True)
def test_end_work_ondemand_should_auto_update_to_available_state(rider_state):
    # Given: READY 상태일 때,
    rider_state.state = RiderState.READY
    # TODO: And: 온디멘드 조건일 때,

    # When: 업무 종료 시,
    rider_state.end_work()

    # Then: READY 상태로 전환된다
    rider_state.refresh_from_db()
    assert rider_state.state == RiderState.AVAILABLE


@pytest.mark.django_db(transaction=True)
def test_end_work_ondemand_should_call_reset(rider_state):
    # Given: READY 상태일 때,
    rider_state.state = RiderState.READY
    # TODO: And: 온디멘드 조건일 때,

    # When: 업무 종료 시,
    mock_reset = Mock()

    # Then: reset 트리거가 실행된다
    with patch.object(rider_state, "reset", mock_reset):
        rider_state.end_work()
        mock_reset.assert_called_once()
