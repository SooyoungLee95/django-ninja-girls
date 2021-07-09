from unittest.mock import patch

import pytest
from django.db.utils import IntegrityError

from ras.rider_app.queries import query_update_rider_availability
from ras.rider_app.schemas import RiderAvailability as RiderAvailabilitySchema
from ras.rideryo.models import RiderAvailabilityHistory


@pytest.mark.django_db(transaction=True)
@patch("ras.common.messaging.helpers.sns_client.publish")
def test_query_update_rider_availability(mock_publish, rider_profile):
    # Given: 기존에 라이더 업무내역 수
    prev_history_count = RiderAvailabilityHistory.objects.filter(rider_id=rider_profile.pk).count()

    # When: 라이더 업무시작/종료 업데이트 요청을 보내면
    data = RiderAvailabilitySchema(is_available=True)
    availability = query_update_rider_availability(data, rider_profile.pk)

    # Then: 요청한 라이더의 업무내역이 반환되고, 요청값이 반영되었는지 확인한다.
    assert availability is not None
    assert availability.rider_id == rider_profile.pk
    assert availability.is_available is True
    # And: 업무내역이 전보다 하나 더 증가한지 확인한다.
    assert prev_history_count + 1 == RiderAvailabilityHistory.objects.filter(rider_id=rider_profile.pk).count()

    # And: rider 근무 상태 이벤트가 발생한다.
    mock_publish.assert_called_once()


@pytest.mark.django_db(transaction=True)
def test_query_update_rider_availability_of_not_existing_rider(rider_profile):
    # Given: 기존에 라이더 업무내역 수
    prev_history_count = RiderAvailabilityHistory.objects.filter(rider_id=rider_profile.pk).count()
    # And: 존재하지 않는 라이더 PK
    not_existing_rider_pk = 9999

    # When: 라이더 업무시작/종료 업데이트 요청을 보내면
    data = RiderAvailabilitySchema(is_available=True)
    try:
        query_update_rider_availability(data, not_existing_rider_pk)
    except IntegrityError:
        # Then: 예외가 발생하고
        assert True
    except Exception:
        raise AssertionError()
    # And: 업무내역이 전과 동일한지 확인한다.
    assert prev_history_count == RiderAvailabilityHistory.objects.filter(rider_id=rider_profile.pk).count()
