from django.conf import settings

from config.settings.base import RIDERYO_BASE_URL

AUTHYO_LOGIN_URL = f"{settings.AUTHYO.BASE_URL}/api/v1/auth/authorize"

RIDER_APP_INITIAL_PASSWORD = "TestTest"

# Mock data
MOCK_TOKEN_PUBLISH_URL = f"http://{RIDERYO_BASE_URL}/api/mock_authyo/authorize"
MOCK_ENCRYPTED_PAYLOAD = "gAAAAABg3SyliEt8iX18AJmeqXEQpIVcAp-5Xz90fZxBppwKydxXsy9ebsNSLUG3ADRljVWtFuliY-vSZQ6l_S0AND-mfxKXJph_LMowCGra3LheTLCPk-m7zcv7dH5te1EYbNSd9CzOqqB9bo9uvT-JWkRXzv0LCyDMJnhi8sxyjyJtk749zjrUttFXsiQ-EfTJGoiK6r2h"  # noqa: E501

MOCK_JWT_ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWJfaWQiOiIxMjM0NTY3ODkwIiwicGxhdGZvcm0iOiJyaWRlcnlvLWRldiIsInJvbGUiOiJyaWRlciIsImV4cCI6MTUxNjIzOTAyMjAsImJhc2VfdXJsIjoiaHR0cDovL2VjMi01Mi03OC05Ni0xNzEuYXAtbm9ydGhlYXN0LTIuY29tcHV0ZS5hbWF6b25hd3MuY29tLyIsImlhdCI6MTUxNjIzOTAyMn0.6HZp4GKVk-tULhytEffSCD9pvvcOPwWTWoZnpVO2mS8"  # noqa: E501
MOCK_JWT_REFRESH_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWJfaWQiOiIxMjM0NTY3ODkwIiwicGxhdGZvcm0iOiJyaWRlcnlvLWRldiIsInJvbGUiOiJyaWRlciIsImV4cCI6MTUxNjIzOTAyMjAwLCJpYXQiOjE1MTYyMzkwMjJ9.7UlNgxGyecI9KVjCxRO1V3rlSD3WGI6KNos9lvF3b7k"  # noqa: E501

MOCK_DISPATCH_REQUEST_ADDITIONAL_INFO_1 = {
    "dispatch_request_id": 123,
    "customer": {
        "phone_number": "010-1111-2222",
        "address": "서초대로38길 12 15층",
        "lat": 37.4899318,
        "lng": 127.0040233,
    },
    "restaurant": {
        "name": "번패티번",
        "detail_name": "번패티번 서초점",
        "address": "서울특별시 서초구 반포대로 27길 21 1층",
        "phone_number": "02-111-2222",
        "lat": 37.4850935,
        "lng": 126.981459,
        "picture_urls": ["http://sample_picture/sample_pickupre/test.jpg"],
    },
    "order": {
        "id": "21052016225297",  # 주문번호(YGY)
        "short_code": "#170",  # 라이더가 주문을 식별하는 코드
        "menu": [
            {"name": "쉬림프 아보카도 버거 세트 X1", "price": 20000, "sub": ["쉬림프 아보카도 버거 X1", "프렌치 프라이 X1", "제로 콜라 X1"]},
            {"name": "치즈 버거 X1", "price": 10900, "sub": ["해시브라운 X1", "버섯 X1", "베이컨 X1"]},
        ],
        "delivery_fee": 9000,
        "total_price": 39900,
        "customer_comment": "일회용 수저, 포크가 필요해요.\n케찹 30개 넣어주세요!! 감사합니다",
        "payment_type": "요기서 결제",
    },
    "estimated_delivery_time": "18:35",  # 배달 예상 시각
    "estimated_pickup_time": "18:25",  # 픽업 예상 시각
    "estimated_delivery_distance": 3.2,  # 배달 예상 거리
    "estimated_delivery_income": 7000,  # 예상 라이더 수수료
    "dispatch_request_created_at": "2021-06-28 18:15:00",  # 배차 생성 시간 화면에 표시하는 용도가 아니라서 포맷 통일하지 않았습니다
}

MOCK_DISPATCH_REQUEST_ADDITIONAL_INFO_2 = {
    "dispatch_request_id": 456,
    "customer": {
        "phone_number": "010-2222-3333",
        "address": "서초대로38길 12 14층",
        "lat": 37.4899318,
        "lng": 127.0040233,
    },
    "restaurant": {
        "name": "번패티번",
        "detail_name": "번패티번 서초점",
        "address": "서울특별시 서초구 반포대로 27길 21 1층",
        "phone_number": "02-111-2222",
        "lat": 37.4850935,
        "lng": 126.981459,
        "picture_urls": ["http://sample_picture/sample_pickupre/test.jpg"],
    },
    "order": {
        "id": "21052016225298",  # 주문번호(YGY)
        "short_code": "#171",  # 라이더가 주문을 식별하는 코드
        "menu": [
            {"name": "쉬림프 아보카도 버거 세트 X1", "price": 20000, "sub": ["쉬림프 아보카도 버거 X1", "프렌치 프라이 X1", "제로 콜라 X1"]},
        ],
        "delivery_fee": 9000,
        "total_price": 29000,
        "customer_comment": "일회용 수저, 포크가 필요해요.\n케찹 30개 넣어주세요!! 감사합니다",
        "payment_type": "요기서 결제",
    },
    "estimated_delivery_time": "18:35",  # 배달 예상 시각
    "estimated_pickup_time": "18:25",  # 픽업 예상 시각
    "estimated_delivery_distance": 3.2,  # 배달 예상 거리
    "estimated_delivery_income": 4000,  # 예상 라이더 수수료
    "dispatch_request_created_at": "2021-06-28 18:16:00",  # 배차 생성 시간 화면에 표시하는 용도가 아니라서 포맷 통일하지 않았습니다
}

MOCK_DISPATCH_REQUEST_ADDITIONAL_INFO_3 = {
    "dispatch_request_id": 789,
    "customer": {
        "phone_number": "010-3333-4444",
        "address": "서초대로38길 12 17층",
        "lat": 37.4899318,
        "lng": 127.0040233,
    },
    "restaurant": {
        "name": "번패티번",
        "detail_name": "번패티번 서초점",
        "address": "서울특별시 서초구 반포대로 27길 21 1층",
        "phone_number": "02-111-2222",
        "lat": 37.4850935,
        "lng": 126.981459,
        "picture_urls": ["http://sample_picture/sample_pickupre/test.jpg"],
    },
    "order": {
        "id": "21052016225299",  # 주문번호(YGY)
        "short_code": "#172",  # 라이더가 주문을 식별하는 코드
        "menu": [
            {"name": "치즈 버거 X1", "price": 10900, "sub": ["해시브라운 X1", "버섯 X1", "베이컨 X1"]},
        ],
        "delivery_fee": 9000,
        "total_price": 19900,
        "customer_comment": "일회용 수저, 포크가 필요해요.\n케찹 30개 넣어주세요!! 감사합니다",
        "payment_type": "요기서 결제",
    },
    "estimated_delivery_time": "18:35",  # 배달 예상 시각
    "estimated_pickup_time": "18:25",  # 픽업 예상 시각
    "estimated_delivery_distance": 3.2,  # 배달 예상 거리
    "estimated_delivery_income": 4000,  # 예상 라이더 수수료
    "dispatch_request_created_at": "2021-06-28 18:17:00",  # 배차 생성 시간 화면에 표시하는 용도가 아니라서 포맷 통일하지 않았습니다
}

CUSTOMER_ISSUE = "고객 요청"
RESTAURANT_ISSUE = "가게 사정"
SYSTEM_ISSUE = "시스템 오류"

CANCEL_REASON_ISSUE_MAP = {
    "customer_cancelled_within_5min": CUSTOMER_ISSUE,
    "not_enough_data": CUSTOMER_ISSUE,
    "customer_canceled": CUSTOMER_ISSUE,
    "long_delivery_time": CUSTOMER_ISSUE,
    "change_closing_hours": RESTAURANT_ISSUE,
    "restaurant_declined": RESTAURANT_ISSUE,
    "restaurant_canceled": RESTAURANT_ISSUE,
    "change_opening_hours": RESTAURANT_ISSUE,
    "back_to_yogiyo_sms_canceled": RESTAURANT_ISSUE,
    "tts_declined": RESTAURANT_ISSUE,
    "out_of_dish": RESTAURANT_ISSUE,
    "restaurant_cant_deliver": RESTAURANT_ISSUE,
    "yogiyo_not_accepted_by_restaurant": RESTAURANT_ISSUE,
    "closing_day": RESTAURANT_ISSUE,
    "change_of_price": RESTAURANT_ISSUE,
    "restaurant_fault": RESTAURANT_ISSUE,
    "rest_closed": RESTAURANT_ISSUE,
    "pos_order_sync_failed": SYSTEM_ISSUE,
    "pos_restaurant_sync_failed": SYSTEM_ISSUE,
    "pos_menu_sync_failed": SYSTEM_ISSUE,
    "pos_deliveryinfo_sync_failed": SYSTEM_ISSUE,
    "not_covered": SYSTEM_ISSUE,
    "tampered_order": SYSTEM_ISSUE,
    "yogiyo_fault": SYSTEM_ISSUE,
    "min_value_changed": SYSTEM_ISSUE,
    "prank_order": SYSTEM_ISSUE,
    "back_to_yogiyo_duplicate": SYSTEM_ISSUE,
    "back_to_yogiyo_prank": SYSTEM_ISSUE,
    "back_to_yogiyo": SYSTEM_ISSUE,
    "other_reasons": SYSTEM_ISSUE,
}

MSG_AGREEMENT_ALREADY_SUBMITTED = "이미 서비스 이용약관에 동의하셨습니다."
MSG_AGREEMENT_NOT_SUBMITTED = "서비스 이용약관에 먼저 동의해주세요."
MSG_MUST_AGREE_REQUIRED_AGREEMENTS = "필수 이용약관에 동의해주세요."
MSG_INVALID_VALUE = "유효하지 않은 값입니다."
MSG_STATE_MACHINE_CANNOT_PROCESS = "해당 작업을 수행할 수 없습니다."

MSG_UNAUTHORIZED = "인증이 유효하지 않습니다."
MSG_NOT_FOUND_RIDER = "라이더를 찾을 수 없습니다."
MSG_NOT_FOUND_PHONE_NUMBER = "등록된 휴대폰 번호가 없습니다."
MSG_FAIL_SENDING_VERIFICATION_CODE = "인증번호 SMS 전송에 실패 하였습니다."
MSG_INVALID_VERIFICATION_CODE = "인증번호가 일치하지 않습니다."
MSG_SUCCESS_CHECKING_VERIFICATION_CODE = "인증이 완료되었습니다."
MSG_INVALID_TOKEN = "유효하지 않은 토큰입니다."
MSG_TOKEN_EXPIRED = "세션이 만료되었습니다. 처음부터 다시 시도해주세요."
MSG_SUCCESS_RESET_PASSWORD = "비밀번호 변경이 완료되었습니다."

YOGIYO_CUSTOMER_CENTER_PHONE_NUMBER = "1661-5270"

VERIFICATION_CODE_TIMEOUT_SECONDS = 300
VERIFY_TOKEN_MAX_AGE = 600

# 최소 8자, 최소 1개의 영 소문자, 대문자,최소 1개의 특수문자, 최소 1개의 숫자
# https://stackoverflow.com/a/21456918
REGEX_PASSWORD_CONDITION = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$"
MAX_PASSWORD_LENGTH = 8
