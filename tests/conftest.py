import pytest

from ras.rideryo.enums import ContractType, DeliveryState
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
    RiderProfile,
    VehicleType,
)


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
