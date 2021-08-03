from unittest.mock import Mock, patch

import pytest

from ras.rideryo.enums import RiderState, RiderTransition


@pytest.mark.django_db(transaction=True)
def test_start_work_ondemand_should_auto_update_to_ready_state(rider_state):
    # Given: AVAILABLE 상태일 때,
    rider_state.state = RiderState.AVAILABLE

    # When: 온디멘드 근무 시작 시,
    rider_state.start_work_ondemand()

    # Then: READY 상태로 전환된다
    rider_state.refresh_from_db()
    assert rider_state.state == RiderState.READY


@pytest.mark.django_db(transaction=True)
def test_start_work_ondemand_should_call_start_dispatch(rider_state):
    # Given: AVAILABLE 상태일 때,
    rider_state.state = RiderState.AVAILABLE

    # When: 온디멘드 근무 시작 시,
    mock_start_dispatch = Mock()

    # Then: start_dispatch 트리거가 실행된다
    with patch.object(rider_state, RiderTransition.ENABLE_NEW_DISPATCH.value, mock_start_dispatch):
        rider_state.start_work_ondemand()
        mock_start_dispatch.assert_called_once()
