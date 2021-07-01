from enum import Enum

from django.db.models import TextChoices


class ContractStatus(TextChoices):
    CONTRACT_REQUEST = "CONTRACT_REQUEST", "계약요청"
    CONTRACT_PENDING = "CONTRACT_PENDING", "계약대기"
    CONTRACT_COMPLETION = "CONTRACT_COMPLETION", "계약완료"
    EMPLOYMENT_COMPLETION = "EMPLOYMENT_COMPLETION", "입직완료"
    EMPLOYMENT_REJECTION = "EMPLOYMENT_REJECTION", "입직반려"
    CONTRACT_TERMINATION = "CONTRACT_TERMINATION", "계약해지"


class ContractType(TextChoices):
    FULL_TIME = "FULL_TIME", "요기요 라이더"
    PART_TIME = "PART_TIME", "요기요 크루"


class Bank(TextChoices):
    # 이용가능 은행 목록: https://rgpkorea.atlassian.net/wiki/spaces/RGP/pages/846431093/API
    SANEOB = ("002", "산업은행")
    GIEOB = ("003", "기업은행")
    GUGMIN = ("004", "국민은행")
    SUHYEOB = ("007", "수협중앙회")
    NONGHYEOP = ("011", "농협은행")
    JIYEOG = ("012", "지역농축협")
    WOORI = ("020", "우리은행")
    SC = ("023", "SC은행")
    CITY = ("027", "한국씨티은행")
    DAEGU = ("031", "대구은행")
    BUSAN = ("032", "부산은행")
    GWANGJU = ("034", "광주은행")
    JEJU = ("035", "제주은행")
    JEONBUK = ("037", "전북은행")
    GYEONGNAM = ("039", "경남은행")
    SAEMAEUL = ("045", "새마을금고연합회")
    SINHYEOB = ("048", "신협")
    JEOCHUG = ("050", "저축은행")
    HSBC = ("054", "HSBC은행")
    DOICHI = ("055", "도이치은행")
    JPMORGAN = ("057", "제이피모간체이스은행")
    BOA = ("060", "BOA은행")
    BNP = ("061", "비엔피파리바은행")
    CHINA_GONGSANG = ("062", "중국공상은행")
    SANLIM = ("064", "산림조합")
    CHINA_GEONSEOL = ("067", "중국건설은행")
    UCHEGUG = ("071", "우체국")
    HANA = ("081", "하나은행")
    SHINHAN = ("088", "신한은행")
    KBANK = ("089", "케이뱅크")
    KAKAO = ("090", "카카오뱅크")


class RiderResponse(TextChoices):
    NOTIFIED = "NOTIFIED", "라이더 배차 전달 완료"
    ACCEPTED = "ACCEPTED", "라이더 주문 수락"
    DECLINED = "DECLINED", "라이더 주문 거절"
    IGNORED = "IGNORED", "라이더 주문 무시"


class DeliveryState(TextChoices):
    NEAR_PICKUP = "NEAR_PICKUP", "픽업지 근처 도착"
    PICK_UP = "PICK_UP", "픽업 완료"
    LEFT_PICKUP = "LEFT_PICKUP", "픽업지 벗어남"
    NEAR_DROPOFF = "NEAR_DROPOFF", "배달지 근처 도착"
    COMPLETED = "COMPLETED", "배달지 도착 완료"


class JungleworksTaskStatus(str, Enum):
    STARTED = "1"
    SUCCESSFUL = "2"
    ACCEPTED = "7"
    DECLINE = "8"
