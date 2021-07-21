from transitions import Machine

from ras.rideryo.enums import RiderState as rs


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
        self.add_transition("start_work_ondemand", rs.AVAILABLE, rs.READY, prepare=self._ondemand_auto_transit)

        # 근무시작 (스케줄)
        self.add_transition("start_work_schedule", rs.AVAILABLE, rs.STARTING)

        # 신규배차 대기중
        self.add_transition("start_dispatch", [rs.STARTING, rs.BREAK], rs.READY)

        # 신규배차 중지
        self.add_transition("end_dispatch", rs.READY, rs.BREAK)

        # 근무종료
        self.add_transition("end_work", [rs.READY, rs.BREAK], rs.ENDING)

        # 근무 대기
        self.add_transition("reset", rs.ENDING, rs.AVAILABLE)

        # 업무정지
        self.add_transition("block", [rs.READY, rs.BREAK], rs.PENDING)

        # 업무정지 해제
        self.add_transition("unblock", rs.PENDING, rs.AVAILABLE)

    def _ondemand_auto_transit(self, *args, **kwargs):
        self.model.state = rs.STARTING
        self._save_model()

    def _save_model(self, *args, **kwargs):
        return self.model.save()
