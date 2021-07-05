import pytest

from ras.rideryo.models import (
    DispatchRequestJungleworksTask,
    RiderAccount,
    RiderDispatchRequestHistory,
    RiderProfile,
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
def dispatch_request_jw_task(rider_dispatch_request):
    tasks = DispatchRequestJungleworksTask.objects.create(
        dispatch_request=rider_dispatch_request, pickup_task_id=1, delivery_task_id=2
    )
    return tasks
