from enum import Enum
from http import HTTPStatus
from unittest.mock import Mock, patch

import pytest
from django.test import Client
from django.urls import reverse

from ras.rider_app.constants import MSG_INVALID_VALUE, MSG_STATE_MACHINE_CANNOT_PROCESS
from ras.rideryo.enums import RiderState as RiderStateEnum
from ras.rideryo.enums import RiderTransition


@pytest.mark.django_db(transaction=True)
def test_action_error_when_invalid_action_is_given(rider_profile, rider_state, mock_jwt_token):
    # Given: 라이더 상태가 저장되어있고
    rider_state.state = RiderStateEnum.APPLYING
    rider_state.save()

    # And: 상태머신에 올바르지 않은 함수명을 등록해둔 경우
    # - mocking한 상태전환 Enum 생성
    dummy_enum = Enum("DummyEnum", list(RiderTransition.__members__), type=str)  # type: ignore[misc]
    # - 더미 값 반환하도록 설정
    dummy_enum.label = property(lambda i: i)  # type: ignore[attr-defined]

    with patch("ras.rideryo.state_machine.rt", dummy_enum):

        # When: 라이더 상태 전환액션 API를 호출 하였을 때
        client = Client()
        response = client.put(
            reverse("ninja:trigger_rider_action", kwargs={"action": RiderTransition.ENABLE_NEW_DISPATCH.value}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {mock_jwt_token}",
        )

    # Then: 400 BAD REQUEST 를 return 해야한다
    assert response.status_code == HTTPStatus.BAD_REQUEST
    data = response.json()
    assert data["message"] == MSG_INVALID_VALUE

    # And: 상태는 그대로 유지된다
    rider_state.refresh_from_db()
    assert rider_state.state == RiderStateEnum.APPLYING


@pytest.mark.django_db(transaction=True)
def test_action_error_when_action_is_not_processable(rider_profile, rider_state, mock_jwt_token):
    # Given: 호출할 액션에서 전환 불가한 라이더 상태인 경우
    rider_state.state = RiderStateEnum.APPLYING
    rider_state.save()

    # When: 라이더 상태 전환액션 API를 호출 하였을 때
    client = Client()
    response = client.put(
        reverse("ninja:trigger_rider_action", kwargs={"action": RiderTransition.ENABLE_NEW_DISPATCH.value}),
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {mock_jwt_token}",
    )

    # Then: 409 CONFLICT 를 return 해야한다
    assert response.status_code == HTTPStatus.CONFLICT
    data = response.json()
    assert data["message"] == MSG_STATE_MACHINE_CANNOT_PROCESS

    # And: 상태는 그대로 유지된다
    rider_state.refresh_from_db()
    assert rider_state.state == RiderStateEnum.APPLYING


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    "valid_state",
    (
        RiderStateEnum.STARTING,
        RiderStateEnum.BREAK,
    ),
)
@patch("ras.common.messaging.publishers.sns_client.publish", Mock(return_value=None))
def test_action_enable_new_dispatch(valid_state, rider_profile, rider_state, mock_jwt_token):
    # Given: 신규 배차 on 가능한 상태에 있는 경우
    rider_state.state = valid_state
    rider_state.save()

    # When: 라이더 상태 전환액션 API를 호출 하였을 때
    client = Client()
    response = client.put(
        reverse("ninja:trigger_rider_action", kwargs={"action": RiderTransition.ENABLE_NEW_DISPATCH.value}),
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {mock_jwt_token}",
    )

    # Then: 200 OK 를 return 해야한다
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data["success"] is True

    # And: 상태는 전환된다
    rider_state.refresh_from_db()
    assert rider_state.state == RiderStateEnum.READY


@pytest.mark.django_db(transaction=True)
@patch("ras.common.messaging.publishers.sns_client.publish", Mock(return_value=None))
def test_action_disable_new_dispatch(rider_profile, rider_state, mock_jwt_token):
    # Given: 신규 배차 off 가능한 상태에 있는 경우
    rider_state.state = RiderStateEnum.READY
    rider_state.save()

    # When: 라이더 상태 전환액션 API를 호출 하였을 때
    client = Client()
    response = client.put(
        reverse("ninja:trigger_rider_action", kwargs={"action": RiderTransition.DISABLE_NEW_DISPATCH.value}),
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {mock_jwt_token}",
    )

    # Then: 200 OK 를 return 해야한다
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data["success"] is True

    # And: 상태는 전환된다
    rider_state.refresh_from_db()
    assert rider_state.state == RiderStateEnum.BREAK


@pytest.mark.django_db(transaction=True)
@patch("ras.common.messaging.publishers.sns_client.publish", Mock(return_value=None))
def test_action_start_work(rider_profile, rider_state, mock_jwt_token):
    # Given: 업무 시작에 가능한 상태에 있는 경우
    rider_state.state = RiderStateEnum.AVAILABLE
    rider_state.save()

    # When: 라이더 상태 전환액션 API를 호출 하였을 때
    client = Client()
    response = client.put(
        reverse("ninja:trigger_rider_action", kwargs={"action": RiderTransition.START_WORK.value}),
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {mock_jwt_token}",
    )

    # Then: 200 OK 를 return 해야한다
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data["success"] is True

    # And: 상태는 전환된다
    rider_state.refresh_from_db()
    assert rider_state.state == RiderStateEnum.READY


@pytest.mark.django_db(transaction=True)
@patch("ras.common.messaging.publishers.sns_client.publish", Mock(return_value=None))
def test_action_end_work(rider_profile, rider_state, mock_jwt_token):
    # Given: 업무 종료 가능한 상태에 있는 경우
    rider_state.state = RiderStateEnum.READY
    rider_state.save()

    # When: 라이더 상태 전환액션 API를 호출 하였을 때
    client = Client()
    response = client.put(
        reverse("ninja:trigger_rider_action", kwargs={"action": RiderTransition.END_WORK.value}),
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {mock_jwt_token}",
    )

    # Then: 200 OK 를 return 해야한다
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data["success"] is True

    # And: 상태는 전환된다
    rider_state.refresh_from_db()
    assert rider_state.state == RiderStateEnum.AVAILABLE
