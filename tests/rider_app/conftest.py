import pytest

from ras.rideryo.models import RiderAccount, RiderProfile


@pytest.fixture
def rider_profile():
    rider_account, _ = RiderAccount.objects.get_or_create(email_address="test@test.com", password="TestTest")
    rider_profile, _ = RiderProfile.objects.get_or_create(
        rider=rider_account,
        full_name="라이더",
        phone_number="01012341234",
        date_of_birth="1999-10-10",
        address="서울시 서초구 방배동",
    )
    return rider_profile
