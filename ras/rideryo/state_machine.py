from transitions import Machine

from ras.rideryo.enums import RiderState

INITIAL = RiderState.INITIAL
APPLYING = RiderState.APPLYING
AVAILABLE = RiderState.AVAILABLE
STARTING = RiderState.STARTING
READY = RiderState.READY
ENDING = RiderState.ENDING
BREAK = RiderState.BREAK
PENDING = RiderState.PENDING


class RiderStateMachine(Machine):
    def __init__(self, model, *args, **kwargs):
        states = [APPLYING, AVAILABLE, STARTING, READY, ENDING, BREAK, PENDING]
        super().__init__(
            model=model,
            states=states,
            send_event=True,
            after_state_change=self._save_model,
            *args,
            **kwargs,
        )

        # 라이더 지원요청
        self.add_transition("apply", INITIAL, APPLYING)

        # 입직승인
        self.add_transition("approve", APPLYING, AVAILABLE)

        # 근무시작 (온디멘드)
        self.add_transition("start_work_ondemand", AVAILABLE, READY, prepare=self._ondemand_auto_transit)

        # 근무시작 (스케줄)
        self.add_transition("start_work_schedule", AVAILABLE, STARTING)

        # 신규배차 대기중
        self.add_transition("start_dispatch", [STARTING, BREAK], READY)

        # 신규배차 중지
        self.add_transition("end_dispatch", READY, BREAK)

        # 근무종료
        self.add_transition("end_work", [READY, BREAK], ENDING)

        # 근무 대기
        self.add_transition("reset", ENDING, AVAILABLE)

        # 업무정지
        self.add_transition("block", [READY, BREAK], PENDING)

        # 업무정지 해제
        self.add_transition("unblock", PENDING, AVAILABLE)

    def _ondemand_auto_transit(self, *args, **kwargs):
        self.model.state = STARTING
        self._save_model()

    def _save_model(self, *args, **kwargs):
        return self.model.save()
