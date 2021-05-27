from unittest.mock import patch

from ras.simulator.management.commands.run_behaviour_tree import Command


@patch("ras.simulator.management.commands.run_behaviour_tree.FleetSimulatorParallel.add_children")
def test_simulator_spawn_multi_riders(mock_simulator_add_children):
    # Given: 총 3명의 라이더 수를 지정하고,
    options = {"debug": False, "export": False, "num": 1, "max": 1}  # default
    expected_rider_count = 3
    options["num"] = expected_rider_count

    # When: 시뮬레이터 실행 시,
    Command().handle(**options)

    # Then: 3명의 라이더가 생성되어 트리에 추가된 것을 확인할 수 있다.
    mock_simulator_add_children.assert_called_once()
    assert len(mock_simulator_add_children.call_args.args[0]) == expected_rider_count


@patch("ras.simulator.management.commands.run_behaviour_tree.call_on_rider_action_change")
@patch("ras.simulator.management.commands.run_behaviour_tree.call_on_rider_location_change")
def test_simulator_call_triggers(mock_location_trigger, mock_action_trigger):
    # When: 시뮬레이터 실행 시,
    options = {"debug": False, "export": False, "num": 1, "max": 1}  # default
    Command().handle(**options)

    # Then: 이벤트 트리거가 발생해야 한다
    mock_action_trigger.assert_called()
    mock_location_trigger.assert_called()

    MIN_CALL_COUNT = 2
    assert mock_action_trigger.call_count >= MIN_CALL_COUNT  # 최소 2번 이상 발생: 배차수락, 배달완료
    assert mock_location_trigger.call_count >= MIN_CALL_COUNT  # 최소 2번 이상 발생: 위 이벤트 발생 시 병렬적으로 호출되어야 함


@patch("ras.simulator.management.commands.run_behaviour_tree.display.render_dot_tree")
def test_simulator_export_diagram(mock_render_tree):
    # Given: export 옵션 활성화하고,
    options = {"debug": False, "export": False, "num": 1, "max": 1}  # default
    options["export"] = True

    # When: 시뮬레이터 실행 시,
    Command().handle(**options)

    # Then: 다이어그램 생성 함수가 호출된다
    mock_render_tree.assert_called_once()
