from transitions import Machine


class RiderStateMachine(Machine):
    def __init__(self):
        states = ["applying", "available", "starting", "ready", "ending", "break", "pending"]
        super().__init__(states=states)

        # 라이더 지원요청
        self.add_transition("apply", "initial", "applying")

        # 입직승인
        self.add_transition("approve", "applying", "available")

        # 근무시작 (온디멘드)
        self.add_transition("start_work_ondemand", "available", "starting", after="start_dispatch")

        # 근무시작 (스케줄)
        self.add_transition("start_work_schedule", "available", "starting")

        # 신규배차 대기중
        self.add_transition("start_dispatch", ["starting", "break"], "ready")

        # 신규배차 중지
        self.add_transition("end_dispatch", "ready", "break")

        # 근무종료
        self.add_transition("end_work", ["ready", "break"], "ending")

        # 근무 대기
        self.add_transition("reset", "ending", "available")

        # 업무정지
        self.add_transition("block", ["ready", "break"], "pending")

        # 업무정지 해제
        self.add_transition("unblock", "pending", "available")
