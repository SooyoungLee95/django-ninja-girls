import jwt
import pytest
from django.conf import settings
from django.db.models import Count

from ras.rideryo.enums import ContractType, DeliveryState, RiderResponse
from ras.rideryo.models import (
    DeliveryCity,
    DeliveryZone,
    DispatchRequestJungleworksTask,
    RiderAccount,
    RiderAvailability,
    RiderContract,
    RiderDeliveryCancelReason,
    RiderDeliveryStateHistory,
    RiderDispatchRequestHistory,
    RiderDispatchResponseHistory,
    RiderProfile,
    VehicleType,
)

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
        order_id="Test_Order",
    )
    return rider_dispatch_request


@pytest.fixture
def rider_dispatch_request_state_near_pickup(rider_dispatch_request):
    delivery_state = RiderDeliveryStateHistory.objects.create(
        dispatch_request=rider_dispatch_request, delivery_state=DeliveryState.NEAR_PICKUP
    )
    return delivery_state


@pytest.fixture
def rider_dispatch_request_state_cancelled(rider_dispatch_request):
    delivery_state = RiderDeliveryStateHistory.objects.create(
        dispatch_request=rider_dispatch_request, delivery_state=DeliveryState.CANCELLED
    )
    RiderDeliveryCancelReason.objects.create(
        dispatch_request=rider_dispatch_request,
        reason="customer_cancelled_within_5min",
    )
    return delivery_state


@pytest.fixture
def rider_dispatch_response(rider_dispatch_request):
    rider_dispatch_response = RiderDispatchResponseHistory.objects.create(
        response=RiderResponse.ACCEPTED,
        dispatch_request=rider_dispatch_request,
    )
    return rider_dispatch_response


@pytest.fixture
def dispatch_request_jw_task(rider_dispatch_request):
    tasks = DispatchRequestJungleworksTask.objects.create(
        dispatch_request=rider_dispatch_request, pickup_task_id=1, delivery_task_id=2
    )
    return tasks


@pytest.fixture
def rider_availability(rider_profile):
    return RiderAvailability.objects.create(rider=rider_profile)


@pytest.fixture
def vehicle_type():
    return VehicleType.objects.create(
        name="오토바이",
        is_active=1,
    )


@pytest.fixture
def delivery_city():
    return DeliveryCity.objects.create(
        name="서울",
        is_active=1,
    )


@pytest.fixture
def delivery_zone(delivery_city):
    return DeliveryZone.objects.create(
        targetyo_zone_id=1,
        name="서초",
        is_active=1,
        delivery_city=delivery_city,
    )


@pytest.fixture
def rider_contract_type(vehicle_type, delivery_zone, rider_profile):
    return RiderContract.objects.create(
        is_active=1,
        delivery_zone=delivery_zone,
        vehicle_type=vehicle_type,
        rider=rider_profile,
        contract_type=ContractType.FULL_TIME,
    )


@pytest.fixture
def notification_data():
    return {
        "Type": "Notification",
        "MessageId": "32137e24-7c24-4478-b5d2-e2a934914881",
        "TopicArn": "arn:aws:sns:us-east-1:000000000000:order",
        "Message": '{"rider_id": 1, "order_id": 1, "reason": "restaurant_cancelled", "event_type": "cancelled"}',
        "Timestamp": "2021-07-13T06:33:41.157Z",
        "SignatureVersion": "1",
        "Signature": "EXAMPLEpH+..",
        "SigningCertURL": "https://sns.us-east-1.amazonaws.com/SimpleNotificationService-0000000000000000000000.pem",
    }


@pytest.fixture
def subscription_data():
    return {
        "Type": "SubscriptionConfirmation",
        "MessageId": "32137e24-7c24-4478-b5d2-e2a934914881",
        "Token": "2336412f37fb687f5d51e6e2...",
        "TopicArn": "arn:aws:sns:us-east-1:000000000000:order",
        "Message": "You have chosen to subscribe to the topic arn:aws:sns:.....\n",
        "SubscribeURL": "https://sns.ap-northeast-2.amazonaws.com/?Action=ConfirmSubscription...",
        "Timestamp": "2021-07-13T06:33:41.157Z",
        "SignatureVersion": "1",
        "Signature": "EXAMPLEpH+..",
        "SigningCertURL": "https://sns.us-east-1.amazonaws.com/SimpleNotificationService-0000000000000000000000.pem",
    }


@pytest.fixture
def unsubscription_data():
    return {
        "Type": "UnsubscribeConfirmation",
        "MessageId": "32137e24-7c24-4478-b5d2-e2a934914881",
        "Token": "2336412f37fb687f5d51e6e2...",
        "TopicArn": "arn:aws:sns:us-east-1:000000000000:order",
        "Message": "You have chosen to deactivate subscription arn:aws:sns:...",
        "SubscribeURL": "https://sns.ap-northeast-2.amazonaws.com/?Action=ConfirmSubscription...",
        "Timestamp": "2021-07-13T06:33:41.157Z",
        "SignatureVersion": "1",
        "Signature": "EXAMPLEpH+..",
        "SigningCertURL": "https://sns.us-east-1.amazonaws.com/SimpleNotificationService-0000000000000000000000.pem",
    }


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


@pytest.fixture
def dummy_rider_dispatch_acceptance_rate(rider_dispatch_response):
    dispatch_accepted = (
        RiderDispatchResponseHistory.objects.filter(
            dispatch_request__rider__rider_id=rider_dispatch_response.dispatch_request.rider_id,
            response=RiderResponse.ACCEPTED,
        )
        .values("dispatch_request__rider__rider_id")
        .annotate(count=Count("id"))
        .values("count")
        .first()
    )
    dispatch_all = (
        RiderDispatchResponseHistory.objects.filter(
            dispatch_request__rider__rider_id=rider_dispatch_response.dispatch_request.rider_id
        )
        .values("dispatch_request__rider__rider_id")
        .annotate(count=Count("id"))
        .values("count")
        .first()
    )
    return round(dispatch_accepted["count"] / dispatch_all["count"] * 100)
