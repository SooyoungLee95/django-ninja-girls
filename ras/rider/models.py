from django.contrib.auth.hashers import make_password
from django.db import models

from ras.rider.enums import Bank
from ras.rider.enums import RiderStatus as RiderStatusEnum


class CommonTimeStamp(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, help_text="생성일자")
    modified_at = models.DateTimeField(auto_now=True, help_text="수정일자")

    class Meta:
        abstract = True


class RiderAccount(CommonTimeStamp):
    """라이더 계정정보"""

    email_address = models.CharField(max_length=100, unique=True, help_text="이메일")
    password = models.CharField(max_length=200)

    def save(self, *args, **kwargs):
        self.password = make_password(self.password)
        super().save(*args, **kwargs)


class RiderProfile(CommonTimeStamp):
    """라이더 프로필"""

    rider_account = models.OneToOneField(
        "RiderAccount", primary_key=True, on_delete=models.DO_NOTHING, help_text="라이더ID"
    )
    contract = models.ForeignKey("Contract", on_delete=models.DO_NOTHING, help_text="계약정보")
    full_name = models.CharField(max_length=100, help_text="이름")
    phone_number = models.CharField(max_length=16, unique=True, null=True, help_text="휴대폰 번호")
    date_of_birth = models.DateField(null=True, help_text="생년월일")
    address = models.CharField(max_length=200, help_text="주소")


class Contract(CommonTimeStamp):
    """라이더 계약정보"""

    delivery_zone = models.ForeignKey("DeliveryZone", on_delete=models.DO_NOTHING, help_text="배달구역 ID")
    vehicle_type = models.ForeignKey("VehicleType", on_delete=models.DO_NOTHING, help_text="운송수단 ID")
    is_active = models.BooleanField(default=True, help_text="활성화여부")


class DeliveryCity(CommonTimeStamp):
    """배달 도시"""

    name = models.CharField(max_length=100, help_text="배달도시명")
    is_active = models.BooleanField(default=True, help_text="활성화여부")


class DeliveryZone(CommonTimeStamp):
    """배달 구역"""

    delivery_city = models.ForeignKey("DeliveryCity", on_delete=models.DO_NOTHING, help_text="배달도시 ID")
    name = models.CharField(max_length=100, help_text="배달구역명")
    is_active = models.BooleanField(default=True, help_text="활성화여부")


class RiderDeliveryZone(CommonTimeStamp):
    """라이더의 배달 구역 정보"""

    rider = models.ForeignKey("RiderAccount", on_delete=models.DO_NOTHING, help_text="라이더 고유ID")
    delivery_zone = models.ForeignKey("DeliveryZone", on_delete=models.DO_NOTHING, help_text="배달구역 고유ID")
    is_main = models.BooleanField(default=False, help_text="메인희망구역 여부")
    is_active = models.BooleanField(default=True, help_text="활성화여부")


class RiderBankAccount(CommonTimeStamp):
    """라이더의 은행 계좌 정보"""

    rider = models.OneToOneField("RiderAccount", primary_key=True, on_delete=models.DO_NOTHING, help_text="라이더ID")
    bank_code = models.CharField(max_length=10, choices=Bank.choices, help_text="은행 코드")
    account_number = models.CharField(max_length=150, help_text="계좌번호")
    account_owner_name = models.CharField(max_length=50, help_text="예금주명")
    is_active = models.BooleanField(default=True, help_text="활성화여부")


class RiderVehicle(CommonTimeStamp):
    """라이더의 운송수단 정보"""

    rider = models.ForeignKey("RiderAccount", on_delete=models.DO_NOTHING, help_text="라이더 ID")
    vehicle_type = models.ForeignKey("VehicleType", on_delete=models.DO_NOTHING, help_text="운송수단 타입 ID")
    vehicle_plate_number = models.CharField(max_length=10, null=True, help_text="차량번호(운송수단이 자동차/스쿠터 등 일때)")
    is_rental = models.BooleanField(default=False, help_text="렌탈여부(ygy에서 렌탈해주는 경우 있음)")
    is_active = models.BooleanField(default=True, help_text="활성화 여부")


class VehicleType(CommonTimeStamp):
    """운송수단 타입"""

    name = models.CharField(max_length=20, help_text="운송수단 명칭")
    is_active = models.BooleanField(default=True, help_text="활성화 여부")


class RiderStatus(CommonTimeStamp):
    """라이더 상태"""

    name = models.CharField(max_length=150, choices=RiderStatusEnum.choices, help_text="라이더 상태명")


class RiderDispatchResultHistory(CommonTimeStamp):
    """라이더 배차 이력 기록"""

    rider = models.ForeignKey("RiderAccount", on_delete=models.DO_NOTHING, help_text="라이더 ID")
    vendor_id = models.CharField(max_length=100, help_text="벤더 ID")
    order_id = models.CharField(max_length=100, help_text="주문 ID")
    dispatch_id = models.CharField(max_length=100, help_text="배차 ID")


class RiderStatusHistory(CommonTimeStamp):
    """라이더 상태 이력 기록"""

    rider = models.ForeignKey("RiderAccount", on_delete=models.DO_NOTHING, help_text="라이더 ID")
    status = models.ForeignKey("RiderStatus", on_delete=models.DO_NOTHING, help_text="라이더 상태 ID")
    dispatch_result = models.ForeignKey(
        RiderDispatchResultHistory, on_delete=models.DO_NOTHING, help_text="라이더 배차 이력 ID"
    )


class Commission(CommonTimeStamp):
    """라이더 수수료"""

    name = models.CharField(max_length=150, help_text="라이더 커미션 명")
    delivery_fee = models.PositiveIntegerField(help_text="라이더 배달 요금")
    is_active = models.BooleanField(default=True, help_text="라이더 커미션 활성화 여부")


class RiderPaymentHistory(CommonTimeStamp):
    """라이더의 정산 정보 기록"""

    rider = models.ForeignKey("RiderAccount", on_delete=models.DO_NOTHING, help_text="라이더 ID")
    commission = models.ForeignKey(Commission, on_delete=models.DO_NOTHING, help_text="라이더 커미션 ID")
    order_id = models.CharField(max_length=100, help_text="주문 ID")


class RiderPaymentResult(CommonTimeStamp):
    """라이더의 정산 정보 조회"""

    rider = models.ForeignKey("RiderAccount", on_delete=models.DO_NOTHING, help_text="라이더 ID")
    rider_evaluation = models.ForeignKey("RiderEvaluation", on_delete=models.DO_NOTHING, help_text="라이더 주문 당 평가 기록 ID")
    order_id = models.CharField(max_length=100, help_text="주문 ID")
    order_created_at = models.DateTimeField()
    amount = models.PositiveIntegerField(help_text="주문에 대한 수수료 요금의 합")


class RiderEvaluation(CommonTimeStamp):
    """각 주문에 대한 라이더의 운행 평가 정보 기록"""

    rider = models.ForeignKey("RiderAccount", on_delete=models.DO_NOTHING, help_text="라이더 ID")
    last_status = models.ForeignKey("RiderStatus", on_delete=models.DO_NOTHING, help_text="라이더의 최종 상태")
    order_id = models.CharField(max_length=100, help_text="주문 ID")
    start_at = models.DateTimeField(help_text="배달 시작 시간")
    end_at = models.DateTimeField(help_text="배달 완료 시간")
    delivery_distance = models.PositiveSmallIntegerField(help_text="총 배달 거리(km)")
