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

blackboard = blackboard.Client(name="Global")
blackboard.register_key(key="action", access=Access.WRITE)
blackboard.action = RiderSimulatedAction.LOGIN


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
    def __init__(self, name="위치전송"):
        super().__init__(name)

    def update(self):
        self.logger.debug(f"  {self.name} [위치전송::update()]")
        call_on_rider_location_change()
        return Status.SUCCESS


class RiderInTransitBehaviour(SuccessEveryN):
    def __init__(self, name="배달상태 확인"):
        ticks_until_delivery_completed = 5
        super().__init__(name, n=ticks_until_delivery_completed)
        self.blackboard = self.attach_blackboard_client(name="RiderInTransitBehaviour")
        self.blackboard.register_key("count", access=Access.WRITE)

    def update(self):
        status = super().update()
        self.logger.debug(f"  {self.name} [배달상태 확인::update()]")
        self.blackboard.count = self.count
        if status == Status.SUCCESS:
            blackboard.action = RiderSimulatedAction.COMPLETE_DELIVERY.name
            call_on_rider_action_change(RiderSimulatedAction.COMPLETE_DELIVERY)
            self.feedback_message = "배달완료"

            # = 다음 배달수락 시, 대기해야 하는 tick 수 랜덤 조절하려면 아래 주석 사용.
            # self.every_n = random.randrange(2, 7)
            # self.count = 0
        else:
            blackboard.action = RiderSimulatedAction.DELIVERYING.name
            self.feedback_message = "배달 중"
        return status

    def terminate(self, new_status):
        if new_status == Status.INVALID:
            self.feedback_message = ""


class RiderNotifiedBehaviour(Behaviour):
    def __init__(self, name="배차 수신여부 확인"):
        super().__init__(name)

    def update(self):
        self.logger.debug(f"  {self.name} [배차 수신여부 확인::update()]")
        if random.random() < 0.3:
            blackboard.action = RiderSimulatedAction.RECEIVE_DELIVERY.name
            self.feedback_message = "배차 수신 완료"
            return Status.SUCCESS
        else:
            blackboard.action = RiderSimulatedAction.WAITING_FOR_DELIVERY.name
            self.feedback_message = "배차 수신 대기중"
            return Status.RUNNING

    def terminate(self, new_status):
        if new_status == Status.INVALID:
            self.feedback_message = ""


class RiderDecidedBehaviour(Behaviour):
    def __init__(self, name="배차 수락/거절 선택"):
        super().__init__(name)

    def update(self):
        self.logger.debug(f"  {self.name} [배차 수락/거절 선택::update()]")
        if random.random() < 0.3:
            blackboard.action = RiderSimulatedAction.ACCEPT_DELIVERY.name
            call_on_rider_action_change(RiderSimulatedAction.ACCEPT_DELIVERY)
            self.feedback_message = "배차 수락"
            return Status.SUCCESS
        else:
            blackboard.action = RiderSimulatedAction.DECLINE_DELIVERY.name
            call_on_rider_action_change(RiderSimulatedAction.DECLINE_DELIVERY)
            self.feedback_message = "배차 거절"
            return Status.FAILURE

    def terminate(self, new_status):
        if new_status == Status.INVALID:
            self.feedback_message = ""


class RiderSimulatorParallel(Parallel):
    pass


class CustomFailureIsRunning(decorators.FailureIsRunning):
    def terminate(self, new_status):
        if new_status == Status.INVALID:
            self.feedback_message = ""


def print_tree(tree):
    print("RiderStatus:", blackboard.action)
    print(display.unicode_tree(root=tree.root, show_status=True))


class Command(BaseCommand):
    help = "Rider Simulator"

    def add_arguments(self, parser):
        parser.add_argument("--export", action="store_true")

    def handle(self, *args, **options):
        # NOTE: Debug 로그 확인 시 아래 주석 사용
        # from py_trees import logging
        # logging.level = logging.Level.DEBUG

        # 배달 프로세스 시퀀스
        #   1. 배차 수신
        #   2. 배차 수락/거절
        #   3. 배달 진행
        delivery_process = Sequence(name="배달 프로세스", memory=True)
        rider_notified = RiderNotifiedBehaviour()
        rider_decided = RiderDecidedBehaviour()
        rider_in_transit = RiderInTransitBehaviour()
        rider_in_transit_until_complete = CustomFailureIsRunning(rider_in_transit, name="배달완료까지 반복")

        delivery_process.add_children([rider_notified, rider_decided, rider_in_transit_until_complete])

        # 위치정보 전송 행동
        location_send = LocationSendBehaviour()

        root = RiderSimulatorParallel(
            "라이더 시뮬레이션",
            policy=ParallelPolicy.SuccessOnAll(synchronise=False),
            children=[delivery_process, location_send],
        )
        root.validate_policy_configuration()
        root.setup_with_descendants()

        behaviour_tree = trees.BehaviourTree(root=root)

        if options["export"]:
            # NOTE: tree diagram render시 아래 주석 사용
            display.render_dot_tree(root=root)
            return

        try:
            MAX_SUCCESS_DELIVERIES = 1
            count = 0
            while count < MAX_SUCCESS_DELIVERIES:
                behaviour_tree.tick(
                    pre_tick_handler=None,
                    post_tick_handler=print_tree,
                )
                if behaviour_tree.root.status == Status.SUCCESS:
                    count += 1
                sleep(1)
        except KeyboardInterrupt:
            behaviour_tree.interrupt()
