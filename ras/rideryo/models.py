from django.contrib.auth.hashers import make_password
from django.db import models

from ras.crypto import decrypt, encrypt
from ras.rideryo.enums import Bank
from ras.rideryo.enums import RiderDeliveryState as RiderDeliveryStateEnum
from ras.rideryo.enums import RiderResponse as RiderResponseEnum


class EncryptCharField(models.CharField):
    def from_db_value(self, value):
        if value is not None:
            return decrypt(value)
        return value

    def get_prep_value(self, value):
        if value is not None:
            return encrypt(value)
        return value


class CommonTimeStamp(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, help_text="생성일자")
    modified_at = models.DateTimeField(auto_now=True, help_text="수정일자")

    class Meta:
        abstract = True


class RiderAccount(CommonTimeStamp):
    """라이더 계정정보"""

    email_address = models.CharField(max_length=100, unique=True, help_text="이메일")
    password = models.CharField(max_length=200, help_text="비밀번호")

    def save(self, *args, **kwargs):
        self.password = make_password(self.password)
        super().save(*args, **kwargs)


class RiderProfile(CommonTimeStamp):
    """라이더 프로필"""

    rider = models.OneToOneField("RiderAccount", primary_key=True, on_delete=models.DO_NOTHING, help_text="라이더 ID")
    full_name = models.CharField(max_length=100, help_text="이름")
    phone_number = models.CharField(max_length=16, help_text="휴대폰 번호")
    date_of_birth = models.DateField(help_text="생년월일")
    address = models.CharField(max_length=200, help_text="주소")


class RiderContract(CommonTimeStamp):
    """라이더 계약정보"""

    rider = models.ForeignKey("RiderProfile", on_delete=models.DO_NOTHING, help_text="라이더 프로필 ID")
    delivery_zone = models.ForeignKey("DeliveryZone", on_delete=models.DO_NOTHING, help_text="배달구역 ID")
    vehicle_type = models.ForeignKey("VehicleType", on_delete=models.DO_NOTHING, help_text="운송수단 ID")
    is_active = models.BooleanField(default=True, help_text="활성화 여부")


class DeliveryCity(CommonTimeStamp):
    """배달 도시"""

    name = models.CharField(max_length=100, help_text="배달도시명")
    is_active = models.BooleanField(default=True, help_text="활성화 여부")


class DeliveryZone(CommonTimeStamp):
    """배달 구역"""

    delivery_city = models.ForeignKey("DeliveryCity", on_delete=models.DO_NOTHING, help_text="배달도시 ID")
    targetyo_zone_id = models.CharField(max_length=10, help_text="targetyo로 부터 받은 배달구역 ID")
    name = models.CharField(max_length=100, help_text="배달구역명")
    is_active = models.BooleanField(default=True, help_text="활성화 여부")


class RiderBankAccount(CommonTimeStamp):
    """라이더의 은행 계좌 정보"""

    rider = models.ForeignKey("RiderProfile", on_delete=models.DO_NOTHING, help_text="라이더 프로필 ID")
    bank_code = models.CharField(max_length=10, choices=Bank.choices, help_text="은행 코드")
    account_number = models.CharField(max_length=150, help_text="계좌번호")
    account_owner_name = models.CharField(max_length=50, help_text="예금주명")
    is_active = models.BooleanField(default=True, help_text="활성화 여부")


class VehicleType(CommonTimeStamp):
    """운송수단 타입"""

    name = models.CharField(max_length=20, help_text="운송수단 명칭")
    is_active = models.BooleanField(default=True, help_text="활성화 여부")


class DeliveryCommission(CommonTimeStamp):
    """배달 수수료"""

    name = models.CharField(max_length=150, help_text="수수료 명")
    fee = models.PositiveIntegerField(help_text="수수료 금액")
    is_active = models.BooleanField(default=True, help_text="배달 수수료 활성화 여부")


class RiderPaymentHistory(CommonTimeStamp):
    """라이더의 정산 정보 기록"""

    dispatch_request = models.ForeignKey("RiderDispatchRequestHistory", on_delete=models.DO_NOTHING, help_text="배차 ID")
    delivery_commission = models.ForeignKey(DeliveryCommission, on_delete=models.DO_NOTHING, help_text="라이더 커미션 ID")


class RiderPaymentResult(CommonTimeStamp):
    """라이더의 정산 정보 조회"""

    rider = models.ForeignKey("RiderProfile", on_delete=models.DO_NOTHING, help_text="라이더 프로필 ID")
    rider_evaluation = models.ForeignKey("RiderEvaluation", on_delete=models.DO_NOTHING, help_text="라이더 주문 당 평가 기록 ID")
    dispatch_request = models.ForeignKey("RiderDispatchRequestHistory", on_delete=models.DO_NOTHING, help_text="배차 ID")
    amount = models.PositiveIntegerField(help_text="배차에 대한 수수료 요금의 합")


class RiderEvaluation(CommonTimeStamp):
    """각 주문에 대한 라이더의 운행 평가 정보 기록"""

    rider = models.ForeignKey("RiderProfile", on_delete=models.DO_NOTHING, help_text="라이더 프로필 ID")
    dispatch_request = models.ForeignKey("RiderDispatchRequestHistory", on_delete=models.DO_NOTHING, help_text="배차 ID")
    start_at = models.DateTimeField(help_text="배달 시작 시간")
    end_at = models.DateTimeField(help_text="배달 완료 시간")
    delivery_distance = models.PositiveSmallIntegerField(help_text="총 배달 거리(km)")


class RiderAvailability(CommonTimeStamp):
    """라이더의 운행 가능여부(운행 가능 / 불가능)"""

    rider = models.OneToOneField("RiderProfile", primary_key=True, on_delete=models.DO_NOTHING, help_text="라이더 프로필 ID")
    is_available = models.BooleanField(default=False)


class RiderAvailabilityHistory(CommonTimeStamp):
    """라이더의 운행 가능여부(운행 가능 / 불가능) 변경 이력"""

    rider = models.ForeignKey("RiderAvailability", on_delete=models.DO_NOTHING, help_text="라이더 운행가능여부 ID")
    is_available = models.BooleanField()


class RiderDispatchRequestHistory(CommonTimeStamp):
    """Dispatchyo로 부터 받은 배차 요청 이력"""

    rider = models.ForeignKey("RiderProfile", on_delete=models.DO_NOTHING, help_text="라이더 프로필 ID")
    vendor_id = models.CharField(max_length=100, help_text="벤더 ID")
    order_id = models.CharField(max_length=100, help_text="주문 ID")
    dispatch_id = models.CharField(max_length=100, unique=True, help_text="배차 ID")


class RiderDispatchResponseHistory(CommonTimeStamp):
    """배차에 대한 라이더의 Response(ACCEPTED/REJECTED/IGNORED) 이력"""

    dispatch_request = models.ForeignKey("RiderDispatchRequestHistory", on_delete=models.DO_NOTHING, help_text="배차 ID")
    response = models.CharField(max_length=150, choices=RiderResponseEnum.choices, help_text="배차에 대한 라이더의 response")


class RiderDeliveryStateHistory(CommonTimeStamp):
    """라이더의 배달 상태(RESTAURANT_ARRIVED/PICKED_UP/DESTINATION_ARRIVED/COMPLETED/NOT_COMPLETED) 이력"""

    dispatch_request = models.ForeignKey("RiderDispatchRequestHistory", on_delete=models.DO_NOTHING, help_text="배차 ID")
    delivery_state = models.CharField(max_length=150, choices=RiderDeliveryStateEnum.choices, help_text="라이더의 배달 상태")


class RiderToken(CommonTimeStamp):
    """라이더 토큰"""

    rider = models.ForeignKey("RiderProfile", on_delete=models.DO_NOTHING, help_text="라이더 프로필 ID")
    registration_token = EncryptCharField(max_length=512, help_text="FCM 발송에 사용되는 토큰")
