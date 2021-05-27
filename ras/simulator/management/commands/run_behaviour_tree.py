import random
from time import sleep

import requests
from django.core.management.base import BaseCommand
from py_trees import blackboard, decorators, display, trees
from py_trees.behaviour import Behaviour
from py_trees.behaviours import SuccessEveryN
from py_trees.common import Access, ParallelPolicy, Status
from py_trees.composites import Parallel, Sequence

from ras.simulator.schemas import RiderSimulatedAction

blackboard.Blackboard.enable_activity_stream(maximum_size=100)
blackboard = blackboard.Client(name="Global")


def call_on_rider_action_change(new_action: RiderSimulatedAction):
    requests.post(
        "http://127.0.0.1:8000/api/simulator/triggers/rider/state",
        json={"rider_id": 0, "action": new_action.value, "location": {"latitude": 0, "longitude": 0}},
    )


def call_on_rider_location_change():
    requests.post(
        "http://127.0.0.1:8000/api/simulator/triggers/rider/location",
        json={"rider_id": 0, "location": {"latitude": 0, "longitude": 0}},
    )


class LocationSendBehaviour(Behaviour):
    def __init__(self, rider_id, name="위치전송"):
        super().__init__(f"[{rider_id}] {name}")

    def update(self):
        self.logger.debug(f"  {self.name} [위치전송::update()]")
        call_on_rider_location_change()
        return Status.SUCCESS


class RiderInTransitBehaviour(SuccessEveryN):
    def __init__(self, rider_id, name="배달지로 이동"):
        ticks_until_delivery_completed = 5
        super().__init__(f"[{rider_id}] {name}", n=ticks_until_delivery_completed)
        self.rider_id = rider_id

    def update(self):
        status = super().update()
        self.logger.debug(f"  {self.name} [배달지로 이동 확인::update()]")
        if status == Status.SUCCESS:
            setattr(blackboard, f"{self.rider_id}/action", RiderSimulatedAction.COMPLETE_DELIVERY.name)
            call_on_rider_action_change(RiderSimulatedAction.COMPLETE_DELIVERY)
            self.feedback_message = "배달완료"

            # = 다음 배달수락 시, 대기해야 하는 tick 수 랜덤 조절하려면 아래 주석 사용.
            # self.every_n = random.randrange(2, 7)
            # self.count = 0
            return status
        else:
            setattr(blackboard, f"{self.rider_id}/action", RiderSimulatedAction.DELIVERYING.name)
            self.feedback_message = "배달 중"
            return Status.RUNNING

    def terminate(self, new_status):
        if new_status == Status.INVALID:
            self.feedback_message = ""


class RiderNotifiedBehaviour(Behaviour):
    def __init__(self, rider_id, name="배차 수신여부 확인"):
        super().__init__(f"[{rider_id}] {name}")
        self.rider_id = rider_id

    def update(self):
        self.logger.debug(f"  {self.name} [배차 수신여부 확인::update()]")
        if random.random() < 0.7:
            setattr(blackboard, f"{self.rider_id}/action", RiderSimulatedAction.RECEIVE_DELIVERY.name)
            self.feedback_message = "배차 수신 완료"
            return Status.SUCCESS
        else:
            setattr(blackboard, f"{self.rider_id}/action", RiderSimulatedAction.WAITING_FOR_DELIVERY.name)
            self.feedback_message = "배차 수신 대기중"
            return Status.RUNNING

    def terminate(self, new_status):
        if new_status == Status.INVALID:
            self.feedback_message = ""


class RiderDecidedBehaviour(Behaviour):
    def __init__(self, rider_id, name="배차 수락/거절 선택"):
        super().__init__(f"[{rider_id}] {name}")
        self.rider_id = rider_id

    def update(self):
        self.logger.debug(f"  {self.name} [배차 수락/거절 선택::update()]")
        if random.random() < 0.7:
            setattr(blackboard, f"{self.rider_id}/action", RiderSimulatedAction.ACCEPT_DELIVERY.name)
            call_on_rider_action_change(RiderSimulatedAction.ACCEPT_DELIVERY)
            self.feedback_message = "배차 수락"
            return Status.SUCCESS
        else:
            setattr(blackboard, f"{self.rider_id}/action", RiderSimulatedAction.DECLINE_DELIVERY.name)
            call_on_rider_action_change(RiderSimulatedAction.DECLINE_DELIVERY)
            self.feedback_message = "배차 거절"
            return Status.FAILURE

    def terminate(self, new_status):
        if new_status == Status.INVALID:
            self.feedback_message = ""


class FleetSimulatorParallel(Parallel):
    pass


class RiderSimulatorParallel(Parallel):
    def __init__(self, rider_id, name="운행 중 (위치/상태 동시전송)", *args, **kwargs):
        super().__init__(f"[{rider_id}] {name}", *args, **kwargs)
        self.rider_id = rider_id
        self.success_delivery = 0

    def update(self):
        if self.status == Status.FAILURE:
            return Status.RUNNING

    def terminate(self, new_status):
        if new_status == Status.SUCCESS:
            self.success_delivery += 1
            setattr(blackboard, f"{self.rider_id}/successful-delivery", self.success_delivery)


class RiderWorkingChecker(decorators.Decorator):
    def __init__(self, child, rider_id, max_deliveries, name="운행완료 여부 확인", *args, **kwargs):
        super().__init__(child, f"[{rider_id}] {name}", *args, **kwargs)
        self.max_deliveries = max_deliveries

    def update(self):
        if self.decorated.success_delivery < self.max_deliveries:
            return Status.RUNNING
        else:
            self.feedback_message = "done."
            return Status.SUCCESS


class CustomFailureIsRunning(decorators.FailureIsRunning):
    def terminate(self, new_status):
        if new_status == Status.INVALID:
            self.feedback_message = ""


def print_tree(tree):
    # NOTE: blackboard 저장 내역 확인 시 아래 주석 사용
    # print(display.unicode_blackboard_activity_stream())
    print(display.unicode_blackboard())
    print(display.unicode_tree(root=tree.root, show_status=True))


class Command(BaseCommand):
    help = "Rider Simulator"

    def add_arguments(self, parser):
        parser.add_argument("--export", action="store_true")
        parser.add_argument("-n", "--num", default=1)
        parser.add_argument("-m", "--max", default=1)
        parser.add_argument("--debug", action="store_true")

    def spawn_rider(self, rider_id):
        # 배달 프로세스 시퀀스
        #   1. 배차 수신
        #   2. 배차 수락/거절
        #   3. 배달 진행
        delivery_process = Sequence(name=f"[{rider_id}] 배달 프로세스", memory=True)
        blackboard.register_key(key=f"{rider_id}/action", access=Access.WRITE)
        setattr(blackboard, f"{rider_id}/action", RiderSimulatedAction.LOGIN)

        blackboard.register_key(key=f"{rider_id}/successful-delivery", access=Access.WRITE)
        setattr(blackboard, f"{rider_id}/successful-delivery", 0)

        rider_notified = RiderNotifiedBehaviour(rider_id)
        rider_decided = RiderDecidedBehaviour(rider_id)
        rider_in_transit = RiderInTransitBehaviour(rider_id)

        delivery_process.add_children([rider_notified, rider_decided, rider_in_transit])

        # 위치정보 전송 행동
        location_send = LocationSendBehaviour(rider_id)

        rider_sim = RiderSimulatorParallel(
            rider_id,
            policy=ParallelPolicy.SuccessOnAll(synchronise=False),
            children=[delivery_process, location_send],
        )

        return rider_sim

    def handle(self, *args, **options):
        if options["debug"]:
            from py_trees import logging

            logging.level = logging.Level.DEBUG

        TOTAL_RIDERS = int(options["num"])
        MAX_SUCCESS_DELIVERIES = int(options["max"])

        fleet_simulator = FleetSimulatorParallel(policy=ParallelPolicy.SuccessOnAll(synchronise=True))
        riders = []
        for rider_id in range(TOTAL_RIDERS):
            rider = self.spawn_rider(rider_id)
            riders.append(RiderWorkingChecker(child=rider, rider_id=rider_id, max_deliveries=MAX_SUCCESS_DELIVERIES))

        fleet_simulator.add_children(riders)
        fleet_simulator.validate_policy_configuration()
        fleet_simulator.setup_with_descendants()
        behaviour_tree = trees.BehaviourTree(root=fleet_simulator)

        if options["export"]:
            display.render_dot_tree(root=fleet_simulator)
            return

        try:
            while behaviour_tree.root.status != Status.SUCCESS:
                behaviour_tree.tick(
                    pre_tick_handler=None,
                    post_tick_handler=print_tree,
                )
                sleep(0.1)
        except KeyboardInterrupt:
            behaviour_tree.interrupt()
