import jwt
import pytest
from django.conf import settings

from ras.rideryo.models import RiderAccount, RiderDispatchRequestHistory, RiderProfile

TEST_JWT_PRIVATE = """-----BEGIN RSA PRIVATE KEY-----
MIICXAIBAAKBgQCJcExoaKfVlIBH6q2IyFbPOCRS5+JfIQWDou3wQ2JadCkglsc8
3g0rc0Yvk8Z9sbFdsi3wnL3dO+3/yklpNO19qICe8ga4bAry70xQNCzxw2GZ8+6j
NFB8vhZ7q24rd27GCP+IKX/sSvi6YU6zkv9UJno9M4ER4mAIz2cETX7rbQIDAQAB
AoGAWWEKj6vf2enlMt/PUvDWY5RjKvdaI/tZlq3ShzmLML/yLxtfHppZfjRNJIu5
vexdKE3DyoJkhwd+U6a97wlYmDHJaNIaR+VWxW9Z1kFThQCxMglEyTjBMQej3m2H
v6lyJEX/ifZtNZ8HrqyqgenYfavviH7E8JRxYwiIvxVp2oECQQDpE5qqT/tQ4sMB
BrqTL7vhdXaBgz//m/wkithtnQKAvHu172ZEslL7liHxbQAd9PfAbz1llpFAZfpf
SS4VSQ+VAkEAlvS5usHNhLA7PABOnLnNgtZUireVe87xzn51doeuNMslrv0ak/Ws
plo5XOr1q+bs0Wi/R6wupZGkLqVxgzDWeQJAGzwpNIGIElmNA8+veYd4Ys4A/P1D
OzEU84gt5hEUu8pKgmXpA1n7DF7stHNSMi3vzVKyT+6aJnZEHWJFukMBSQJAS/9U
6gLb1utqRuDYsuqP3kjNMzENntEmx5C+zjesqoODqz9dfBP5IZ7WtkLMAAk4PI0B
j7HNoilagOll5mhV8QJBAKvzEsWMeQkgmd5ZgoSAx5xDgJ5YUUTC9qqwjqYSZCE1
3g/BzhMvc9aht6HWon+M+g5S93ePit89SxK4GGEpnEs=
-----END RSA PRIVATE KEY-----"""


@pytest.fixture
def rider_profile():
    rider_account = RiderAccount.objects.create(email_address="test@test.com", password="TestTest")
    rider_profile = RiderProfile.objects.create(
        rider=rider_account,
        full_name="라이더",
        phone_number="01012341234",
        date_of_birth="1999-10-10",
        address="서울시 서초구 방배동",
    )
    return rider_profile


@pytest.fixture
def rider_dispatch_request(rider_profile):
    rider_dispatch_request = RiderDispatchRequestHistory.objects.create(
        rider=rider_profile,
        vendor_id="Test",
        order_id="Test_Order",
        dispatch_id=1,
    )
    return rider_dispatch_request


def _generate_payload(role):
    return {
        "iat": 1625703402,
        "exp": 2247783524,
        "sub_id": 1,
        "platform": settings.RIDERYO_BASE_URL,
        "base_url": settings.RIDERYO_ENV,
        "role": role,
    }


@pytest.fixture
def mock_jwt_token():
    return jwt.encode(
        _generate_payload("rider"),
        TEST_JWT_PRIVATE,
        algorithm="RS256",
    )


@pytest.fixture
def mock_jwt_token_with_staff():
    return jwt.encode(
        _generate_payload("staff"),
        TEST_JWT_PRIVATE,
        algorithm="RS256",
    )
