import logging

from transitions import Machine

from ras.common.messaging.consts import RIDER_WORKING_STATE
from ras.common.messaging.publishers import publish_rider_working_state
from ras.rideryo.enums import RiderState as rs
from ras.rideryo.enums import RiderTransition as rt

logger = logging.getLogger(__name__)
event_type_publish_func = {RIDER_WORKING_STATE: publish_rider_working_state}


class RiderStateMachine(Machine):
    def __init__(self, model, *args, **kwargs):
        states = [rs.APPLYING, rs.AVAILABLE, rs.STARTING, rs.READY, rs.ENDING, rs.BREAK, rs.PENDING]
        super().__init__(
            model=model,
            states=states,
            send_event=True,
            after_state_change=self._save_model,
            *args,
            **kwargs,
        )

        # 라이더 지원요청
        self.add_transition("apply", rs.INITIAL, rs.APPLYING)

        # 입직승인
        self.add_transition("approve", rs.APPLYING, rs.AVAILABLE)

        # 근무시작 (온디멘드)
        self.add_transition("start_work_ondemand", rs.AVAILABLE, rs.STARTING)

        # 근무시작 (스케줄)
        self.add_transition("start_work_schedule", rs.AVAILABLE, rs.STARTING)

        # 신규배차 대기중
        self.add_transition(rt.ENABLE_NEW_DISPATCH, [rs.STARTING, rs.BREAK], rs.READY)

        # 신규배차 중지
        self.add_transition(rt.DISABLE_NEW_DISPATCH, rs.READY, rs.BREAK)

        # 근무종료
        self.add_transition("end_work", [rs.READY, rs.BREAK], rs.ENDING)

        # 근무 대기
        self.add_transition("reset", rs.ENDING, rs.AVAILABLE)

        # 업무정지
        self.add_transition("block", [rs.READY, rs.BREAK], rs.PENDING)

        # 업무정지 해제
        self.add_transition("unblock", rs.PENDING, rs.AVAILABLE)

        # 상태별 콜백 추가
        self._add_state_callbacks()

    def _add_state_callbacks(self):
        # 근무시작/종료 SNS 이벤트 발송
        self.on_enter_READY(self.handle_READY)
        self.on_exit_READY(self.handle_READY)

    def _save_model(self, *args, **kwargs):
        self.model.save()
        event_data = args[0]
        logger.info(
            f"Rider:{self.model.rider.pk} {event_data.event.name} "
            f"[{event_data.transition.source} -> {event_data.transition.dest}]"
        )
        if event_data.event.name == "start_work_ondemand":
            getattr(self.model, rt.ENABLE_NEW_DISPATCH.value)()

    def handle_READY(self, event_data, *args, **kwargs):
        publish_rider_working_state(event_data.model)
