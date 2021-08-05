import json
from http import HTTPStatus
from unittest.mock import Mock, patch

import orjson
import pytest
import transitions
from django.conf import settings
from django.db.utils import IntegrityError
from django.test import Client
from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time

from ras.common.integration.services.jungleworks.schemas import JungleworksResponseBody
from ras.rider_app.constants import (
    CUSTOMER_ISSUE,
    MSG_AGREEMENT_ALREADY_SUBMITTED,
    MSG_AGREEMENT_NOT_SUBMITTED,
    MSG_MUST_AGREE_REQUIRED_AGREEMENTS,
)
from ras.rider_app.enums import PushAction
from ras.rider_app.schemas import RiderBan, RiderDeliveryState, RiderDispatchResponse
from ras.rideryo.enums import DeliveryState
from ras.rideryo.enums import RiderState as RiderStateEnum
from ras.rideryo.enums import ServiceAgreementType
from ras.rideryo.models import RiderDeliveryStateHistory, RiderServiceAgreement


class TestRiderDispatchResponse:
    def _call_api_create_rider_dispatch_response(self, input_body, jwt_token):
        client = Client()

        return client.post(
            reverse("ninja:create_rider_dispatch_response"),
            data=input_body.dict(),
            content_type="application/json",
            **{"HTTP_AUTHORIZATION": f"Bearer {jwt_token}"},
        )

    def _make_request_body(self, dispatch_request_id, response):
        return RiderDispatchResponse(dispatch_request_id=dispatch_request_id, response=response)

    @pytest.mark.django_db(transaction=True)
    @patch("ras.rider_app.views.should_connect_jungleworks")
    def test_create_rider_dispatch_when_jw_enabled(self, mock_use_jungleworks, rider_dispatch_request, mock_jwt_token):
        # Given: Jungleworks 기능이 활성화되고,
        mock_use_jungleworks.return_value = True
        # And: Jungleworks API에서 성공 응답을 반환하는 경우
        expected_jungleworks_response = JungleworksResponseBody(message="test-message", status=200, data={})

        # When: 라이더 배차 수락 API 호출 시,
        with patch("ras.rider_app.helpers.update_task_status") as mock_update_task_status:
            mock_update_task_status.return_value = expected_jungleworks_response
            input_body = self._make_request_body(rider_dispatch_request.id, "ACCEPTED")
            response = self._call_api_create_rider_dispatch_response(input_body, jwt_token=mock_jwt_token)

        # Then: Jungleworks 응답코드에 상응하는 응답코드가 반환된다.
        assert response.status_code == expected_jungleworks_response.relevant_http_status()

        # And: Jungleworks 활성화 체크 함수 및 응답값이 올바른지 확인한다.
        mock_use_jungleworks.assert_called_once()
        assert response.json() == input_body.dict()

        # And: RiderDeliveryStateHistory 값이 생성되어야 한다
        delivery_state = RiderDeliveryStateHistory.objects.filter(
            dispatch_request=rider_dispatch_request, delivery_state=DeliveryState.ACCEPTED
        ).first()
        assert delivery_state is not None

    @pytest.mark.django_db(transaction=True)
    @patch("ras.rider_app.views.should_connect_jungleworks")
    def test_create_rider_dispatch_when_jw_not_enabled(
        self, mock_use_jungleworks, rider_dispatch_request, mock_jwt_token
    ):
        # Given: Jungleworks 기능이 비활성화된 경우
        mock_use_jungleworks.return_value = False

        # When: 라이더 배차 수락 API 호출 시,
        input_body = self._make_request_body(rider_dispatch_request.id, "ACCEPTED")
        response = self._call_api_create_rider_dispatch_response(input_body, mock_jwt_token)

        # Then: 200 응답코드가 반환되고,
        assert response.status_code == HTTPStatus.OK

        # And: Jungleworks 활성화 체크 함수 및 응답값이 올바른지 확인한다.
        mock_use_jungleworks.assert_called_once()
        assert response.json() == input_body.dict()

        # And: RiderDeliveryStateHistory 값이 생성되어야 한다
        delivery_state = RiderDeliveryStateHistory.objects.filter(
            dispatch_request=rider_dispatch_request, delivery_state=DeliveryState.ACCEPTED
        ).first()
        assert delivery_state is not None

    @pytest.mark.django_db(transaction=True)
    @patch("ras.rider_app.views.should_connect_jungleworks")
    def test_update_rider_dispatch_error_when_jw_enabled(
        self, mock_use_jungleworks, rider_dispatch_request, mock_jwt_token
    ):
        # Given: Jungleworks 기능이 활성화되고,
        mock_use_jungleworks.return_value = True
        # And: Jungleworks API에서 에러 응답을 반환하는 경우
        expected_jungleworks_response = JungleworksResponseBody(message="invalid", status=100, data={})

        # When: 라이더 배차 수락 API 호출 시,
        with patch("ras.rider_app.helpers.update_task_status") as mock_update_task_status:
            mock_update_task_status.return_value = expected_jungleworks_response
            input_body = self._make_request_body(rider_dispatch_request.id, "ACCEPTED")
            response = self._call_api_create_rider_dispatch_response(input_body, jwt_token=mock_jwt_token)

        # Then: Jungleworks 응답코드에 상응하는 응답코드가 반환되고,
        assert response.status_code == expected_jungleworks_response.relevant_http_status()
        # And: Jungleworks 활성화 체크 함수 및 응답값이 올바른지 확인한다.
        mock_use_jungleworks.assert_called_once()
        assert response.json() == {"message": "invalid"}

    @pytest.mark.django_db(transaction=True)
    @patch("ras.rider_app.views.should_connect_jungleworks")
    def test_update_rider_dispatch_error_when_jw_not_enabled(
        self, mock_use_jungleworks, rider_dispatch_request, mock_jwt_token
    ):
        # Given: Jungleworks 기능이 비활성화된 경우
        mock_use_jungleworks.return_value = False

        # When: 라이더 배차 수락 API 호출 시,
        with patch("ras.rider_app.helpers.query_create_rider_dispatch_response") as mock_query_create:
            # DB 조회시 에러 발생
            mock_query_create.side_effect = IntegrityError()
            input_body = self._make_request_body(rider_dispatch_request.id, "ACCEPTED")
            response = self._call_api_create_rider_dispatch_response(input_body, jwt_token=mock_jwt_token)

        # Then: 400 응답코드가 반환된다.
        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert response.json() == {"message": "유효한 ID 값이 아닙니다."}

    @pytest.mark.django_db(transaction=True)
    @patch("ras.rider_app.views.should_connect_jungleworks")
    def test_create_rider_dispatch_notified_when_jw_enabled(
        self, mock_use_jungleworks, rider_dispatch_request, mock_jwt_token
    ):
        # Given: Jungleworks 기능이 활성화되고,
        mock_use_jungleworks.return_value = True
        # And: Jungleworks API에서 성공 응답을 반환하는 경우
        expected_jungleworks_response = JungleworksResponseBody(message="test-message", status=200, data={})

        # When: 라이더 배차 확인 완료 API 호출 시,
        with patch("ras.rider_app.helpers.update_task_status") as mock_update_task_status:
            mock_update_task_status.return_value = expected_jungleworks_response
            input_body = self._make_request_body(rider_dispatch_request.id, "NOTIFIED")
            response = self._call_api_create_rider_dispatch_response(input_body, jwt_token=mock_jwt_token)

        # Then: Jungleworks update_task_status API가 호출되지 않고,
        assert mock_update_task_status.call_count == 0
        # AND: Jungleworks 응답코드에 상응하는 응답코드가 반환된다.
        assert response.status_code == expected_jungleworks_response.relevant_http_status()

        # And: Jungleworks 활성화 체크 함수 및 응답값이 올바른지 확인한다.
        mock_use_jungleworks.assert_called_once()
        assert response.json() == input_body.dict()

        # And: RiderDeliveryStateHistory 값이 생성되어야 한다
        delivery_state = RiderDeliveryStateHistory.objects.filter(
            dispatch_request=rider_dispatch_request, delivery_state=DeliveryState.NOTIFIED
        ).first()
        assert delivery_state is not None

    @pytest.mark.django_db(transaction=True)
    @patch("ras.rider_app.views.should_connect_jungleworks")
    def test_create_rider_dispatch_notified_when_jw_not_enabled(
        self, mock_use_jungleworks, rider_dispatch_request, mock_jwt_token
    ):
        # Given: Jungleworks 기능이 비활성화된 경우
        mock_use_jungleworks.return_value = False

        # When: 라이더 배차 확인 완료 API 호출 시,
        input_body = self._make_request_body(rider_dispatch_request.id, "NOTIFIED")
        response = self._call_api_create_rider_dispatch_response(input_body, mock_jwt_token)

        # Then: 200 응답코드가 반환되고,
        assert response.status_code == HTTPStatus.OK

        # And: Jungleworks 활성화 체크 함수 및 응답값이 올바른지 확인한다.
        mock_use_jungleworks.assert_called_once()
        assert response.json() == input_body.dict()

        # And: RiderDeliveryStateHistory 값이 생성되어야 한다
        delivery_state = RiderDeliveryStateHistory.objects.filter(
            dispatch_request=rider_dispatch_request, delivery_state=DeliveryState.NOTIFIED
        ).first()
        assert delivery_state is not None


class TestRiderDeliveryState:
    def _call_api_create_rider_delivery_state(self, input_body, token):
        client = Client()

        return client.post(
            reverse("ninja:create_rider_delivery_state"),
            data=input_body.dict(),
            content_type="application/json",
            **{"HTTP_AUTHORIZATION": f"Bearer {token}"},
        )

    def _make_request_body(self, dispatch_request_id, state):
        return RiderDeliveryState(dispatch_request_id=dispatch_request_id, state=state)

    @pytest.mark.parametrize(
        "state, expected_jw_calls",
        [
            (DeliveryState.PICK_UP, 2),
            (DeliveryState.COMPLETED, 1),
        ],
    )
    @pytest.mark.django_db(transaction=True)
    @patch("ras.rider_app.views.should_connect_jungleworks")
    @patch("ras.rider_app.views.mock_delivery_state_push_action", Mock(return_value=None))
    def test_create_rider_delivery_state_when_jw_enabled(
        self,
        mock_use_jungleworks,
        rider_dispatch_request,
        dispatch_request_jw_task,
        state,
        expected_jw_calls,
        mock_jwt_token,
    ):
        # Given: Jungleworks 기능이 활성화되고,
        mock_use_jungleworks.return_value = True
        # And: Jungleworks API에서 성공 응답을 반환하는 경우
        expected_jungleworks_response = JungleworksResponseBody(message="test-message", status=200, data={})

        # When: 배달 상태 전달 API 호출 시,
        with patch(
            "ras.common.integration.services.jungleworks.handlers._update_task_status"
        ) as mock_jw_update_task_status:
            mock_jw_update_task_status.return_value = expected_jungleworks_response
            input_body = self._make_request_body(rider_dispatch_request.id, state)
            response = self._call_api_create_rider_delivery_state(input_body, mock_jwt_token)

            # 픽업 task SUCCESSFUL, 배달 task START 로 전환하는 요청 총 2개가 호출됩니다.
            assert mock_jw_update_task_status.call_count == expected_jw_calls

        # Then: Jungleworks 응답코드에 상응하는 응답코드가 반환된다.
        assert response.status_code == expected_jungleworks_response.relevant_http_status()

        # And: Jungleworks 활성화 체크 함수 및 응답값이 올바른지 확인한다.
        mock_use_jungleworks.assert_called_once()
        assert response.json() == input_body.dict()

        # And: 상태 변경에 대한 이력이 기록되는지 확인합니다.
        history = (
            RiderDeliveryStateHistory.objects.filter(dispatch_request=rider_dispatch_request)
            .order_by("-created_at")
            .first()
        )
        assert history.delivery_state == state

    @pytest.mark.parametrize(
        "state",
        [
            DeliveryState.PICK_UP,
            DeliveryState.COMPLETED,
        ],
    )
    @pytest.mark.django_db(transaction=True)
    @patch("ras.rider_app.views.should_connect_jungleworks")
    @patch("ras.rider_app.views.mock_delivery_state_push_action", Mock(return_value=None))
    def test_create_rider_delivery_state_when_jw_not_enabled(
        self, mock_use_jungleworks, rider_dispatch_request, state, mock_jwt_token
    ):
        # Given: Jungleworks 기능이 비활성화된 경우
        mock_use_jungleworks.return_value = False

        # When: 배달 상태 전달 API 호출 시,
        input_body = self._make_request_body(rider_dispatch_request.id, state)
        response = self._call_api_create_rider_delivery_state(input_body, mock_jwt_token)

        # Then: 200 응답코드가 반환되고,
        assert response.status_code == HTTPStatus.OK

        # And: Jungleworks 활성화 체크 함수 및 응답값이 올바른지 확인한다.
        mock_use_jungleworks.assert_called_once()
        assert response.json() == input_body.dict()

        # And: 상태 변경에 대한 이력이 기록되는지 확인합니다.
        history = (
            RiderDeliveryStateHistory.objects.filter(dispatch_request=rider_dispatch_request)
            .order_by("-created_at")
            .first()
        )
        assert history.delivery_state == state

    @pytest.mark.parametrize(
        "state, should_send_push, push_action",
        [
            (DeliveryState.NEAR_PICKUP, True, PushAction.NEAR_PICKUP),
            (DeliveryState.PICK_UP, False, None),
            (DeliveryState.NEAR_DROPOFF, True, PushAction.NEAR_DROPOFF),
            (DeliveryState.COMPLETED, False, None),
        ],
    )
    @pytest.mark.django_db(transaction=True)
    @patch("ras.rider_app.views.should_connect_jungleworks", Mock(return_value=False))
    @patch("ras.rider_app.helpers.send_push_action")
    def test_create_rider_delivery_state_should_send_push(
        self, mock_fcm_send, rider_dispatch_request, state, should_send_push, push_action, mock_jwt_token
    ):
        # Given: 배달 상태가 변경된 경우
        input_body = self._make_request_body(rider_dispatch_request.id, state)

        # When: 배달 상태 전달 API 호출 시,
        response = self._call_api_create_rider_delivery_state(input_body, mock_jwt_token)

        # Then: 상태에 따라 푸시가 발생한다.
        if should_send_push:
            mock_fcm_send.assert_called_once()
            assert mock_fcm_send.call_args.kwargs["action"] == push_action
        else:
            mock_fcm_send.assert_not_called()

        # And: 200 응답코드가 반환된다.
        assert response.status_code == HTTPStatus.OK


class TestRiderBan:
    def _call_api_update_rider_ban(self, input_body, token):
        client = Client()

        return client.put(
            reverse("ninja:rider_app_update_rider_ban"),
            data=input_body.dict(),
            content_type="application/json",
            **{"HTTP_AUTHORIZATION": f"Bearer {token}"},
        )

    def _make_request_body(self, rider_id, is_banned):
        return RiderBan(rider_id=rider_id, is_banned=is_banned)

    @pytest.mark.parametrize(
        "given_rider_availability, given_state",
        [
            (True, RiderStateEnum.READY),
            (False, RiderStateEnum.BREAK),
        ],
    )
    @pytest.mark.django_db(transaction=True)
    @patch("ras.rider_app.views.should_connect_jungleworks", Mock(return_value=False))
    @patch("ras.rider_app.helpers.send_push_action", Mock(return_value=None))
    @patch("ras.common.messaging.publishers.sns_client.publish")
    def test_update_rider_ban_should_change_rider_to_unavailable(
        self,
        mock_publish,
        given_rider_availability,
        mock_jwt_token_with_staff,
        given_state,
        rider_profile,
        rider_state,
    ):

        # Given: 라이더가 "근무 중"이거나 "근무 중이 아닌" 상태일 때,
        rider_state.state = given_state
        rider_state.save()

        # And: 업무정지 된 경우
        input_body = self._make_request_body(rider_state.rider.pk, is_banned=True)

        # When: 업무정지 API 호출 시,
        response = self._call_api_update_rider_ban(input_body, mock_jwt_token_with_staff)

        # And: 200 응답코드가 반환된다.
        assert response.status_code == HTTPStatus.OK

        # And: rider 근무 상태 이벤트가 발생한다.
        if given_state == RiderStateEnum.READY:
            mock_publish.assert_called_once()

        # And: 라이더 상태가 Pending으로 전환된다
        rider_state.refresh_from_db()
        assert rider_state.state == RiderStateEnum.PENDING

    @pytest.mark.django_db(transaction=True)
    @patch("ras.rider_app.views.should_connect_jungleworks", Mock(return_value=False))
    @patch("ras.rider_app.helpers.send_push_action", Mock(return_value=None))
    def test_update_rider_undo_ban_should_change_from_pending_to_available(
        self, mock_jwt_token_with_staff, rider_profile, rider_state
    ):
        # Given: 라이더 상태가 Pending 이고,
        rider_state.state = RiderStateEnum.PENDING
        rider_state.save()

        # And: 업무정지 해제가 된 경우
        input_body = self._make_request_body(rider_state.rider.pk, is_banned=False)

        # When: 업무정지 API 호출 시,
        response = self._call_api_update_rider_ban(input_body, mock_jwt_token_with_staff)

        # Then: 200 응답코드가 반환된다.
        assert response.status_code == HTTPStatus.OK

        # And: 라이더 상태가 Available로 전환된다
        rider_state.refresh_from_db()
        assert rider_state.state == RiderStateEnum.AVAILABLE

    @pytest.mark.django_db(transaction=True)
    @patch("ras.rider_app.views.should_connect_jungleworks", Mock(return_value=False))
    @patch("ras.rider_app.helpers.send_push_action", Mock(return_value=None))
    def test_update_rider_undo_ban_should_raise_error_when_state_is_not_pending(
        self, mock_jwt_token_with_staff, rider_profile, rider_state
    ):
        # Given: 라이더 상태가 Ready 이고,
        rider_state.state = RiderStateEnum.READY
        rider_state.save()

        # And: 업무정지 해제가 된 경우
        input_body = self._make_request_body(rider_state.rider.pk, is_banned=False)

        # When: 업무정지 API 호출 시,
        try:
            self._call_api_update_rider_ban(input_body, mock_jwt_token_with_staff)
        except transitions.core.MachineError:
            # Then: 에러가 발생한다.
            # TODO: 에러 처리
            pass
        except Exception:
            raise AssertionError()
        else:
            raise AssertionError()

    @pytest.mark.parametrize(
        "is_banned, push_action",
        [
            (True, PushAction.BAN),
            (False, PushAction.UNDO_BAN),
        ],
    )
    @pytest.mark.django_db(transaction=True)
    @patch("ras.rider_app.views.should_connect_jungleworks", Mock(return_value=False))
    @patch("ras.rider_app.helpers.send_push_action")
    @patch("ras.common.messaging.publishers.sns_client.publish", Mock(return_value=None))
    def test_update_rider_ban_should_send_push(
        self,
        mock_fcm_send,
        rider_profile,
        is_banned,
        push_action,
        mock_jwt_token_with_staff,
        rider_state,
    ):
        rider_state.state = RiderStateEnum.READY if is_banned else RiderStateEnum.PENDING
        rider_state.save()

        # Given: 업무정지 상태가 변경된 경우
        input_body = self._make_request_body(rider_profile.pk, is_banned)

        # When: 업무정지 API 호출 시,
        response = self._call_api_update_rider_ban(input_body, mock_jwt_token_with_staff)

        # Then: 올바른 푸시가 발생한다.
        mock_fcm_send.assert_called_once()
        assert mock_fcm_send.call_args.kwargs["action"] == push_action

        # And: 200 응답코드가 반환된다.
        assert response.status_code == HTTPStatus.OK

    @pytest.mark.parametrize("is_banned", [True, False])
    @pytest.mark.django_db(transaction=True)
    @patch("ras.rider_app.views.should_connect_jungleworks", Mock(return_value=False))
    @patch("ras.rider_app.helpers.send_push_action", Mock(return_value=None))
    def test_update_rider_ban_should_return_403_when_token_role_is_not_staff(
        self, mock_jwt_token, rider_profile, is_banned
    ):
        # Given: 업무정지 상태가 변경된 경우
        input_body = self._make_request_body(rider_profile.pk, is_banned=is_banned)

        # When: 업무정지 API 호출 시,
        response = self._call_api_update_rider_ban(input_body, mock_jwt_token)

        # Then: 403 응답코드가 반환된다.
        assert response.status_code == HTTPStatus.FORBIDDEN


@pytest.mark.django_db(transaction=True)
def test_retrieve_rider_profile_summary(dummy_rider_profile, mock_jwt_token):
    # When: 라이더 프로필 조회 API를 호출 하였을 때
    client = Client()
    response = client.get(
        reverse("ninja:retrieve_rider_profile_summary"),
        **{"HTTP_AUTHORIZATION": f"Bearer {mock_jwt_token}"},
    )
    # Then: 200 OK를 return 해야하고,
    assert response.status_code == HTTPStatus.OK
    # And: 라이더 프로필 정보가 일치해야한다.
    assert response.json() == dummy_rider_profile


@pytest.mark.django_db(transaction=True)
@patch("ras.rider_app.helpers.query_get_rider_profile_summary", Mock(return_value=None))
def test_retrieve_rider_profile_summary_when_rider_profile_does_not_exist(rider_contract_type, mock_jwt_token):
    # When: 라이더 프로필 조회 API를 호출 하였을 때
    client = Client()
    response = client.get(
        reverse("ninja:retrieve_rider_profile_summary"),
        **{"HTTP_AUTHORIZATION": f"Bearer {mock_jwt_token}"},
    )
    # Then: 404 NOT_FOUND를 return 해야하고,
    assert response.status_code == HTTPStatus.NOT_FOUND
    # And: message는 라이더가 존재하지 않습니다. 이어야 한다
    assert json.loads(response.content)["message"] == "라이더가 존재하지 않습니다."


@pytest.mark.django_db(transaction=True)
@patch("ras.rider_app.helpers.send_push_action")
@patch("ras.rider_app.views.handle_sns_notification")
def test_subscribe_sns_event_order_cancelled(
    mock_handler, mock_push, rider_dispatch_request, notification_data, mock_jwt_token
):
    # Given: Order-Cancelled notification 생성
    rider_id = rider_dispatch_request.rider.pk
    order_id = rider_dispatch_request.order_id
    reason = "restaurant_cancelled"

    body = notification_data
    body["TopicArn"] = settings.ARN_SNS_TOPIC_ORDER
    body["Message"] = orjson.dumps(
        {"rider_id": rider_id, "order_id": order_id, "reason": reason, "event_type": "cancelled"}
    ).decode()

    # And: 이벤트 처리 함수 mocking
    mock_handler.return_value = rider_dispatch_request

    # When: 메시지가 게시되면,
    client = Client()
    response = client.post(
        reverse("ninja:rider_app_sns_notification", kwargs={"topic": "order"}),
        data=body,
        content_type="application/json",
        **{"HTTP_AUTHORIZATION": f"Bearer {mock_jwt_token}"},
    )

    # Then: 성공 응답 반환되고,
    assert response.status_code == HTTPStatus.OK

    # And: 이벤트 핸들러 및 푸시발송이 실행된다
    mock_handler.assert_called_once()
    mock_push.assert_called_once()


@pytest.mark.django_db(transaction=True)
def test_dispatch_requests_detail_not_cancelled(
    rider_dispatch_request, rider_dispatch_request_state_near_pickup, mock_jwt_token
):
    # Given: 배차정보 및 상태기록이 있고

    # When: 배차 정보 조회 시,
    client = Client()
    response = client.get(
        reverse("ninja:mock_rider_app_dispatch_requests_detail") + f"?id={rider_dispatch_request.pk}",
        content_type="application/json",
        **{"HTTP_AUTHORIZATION": f"Bearer {mock_jwt_token}"},
    )

    # Then: 200 성공 응답, 배열이 반환되고
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert isinstance(data, list)

    # Then: 올바른 값이 포함되어 있고, 배차정보 및 상태가 반환된다
    detail = data[0]
    assert detail["dispatch_request_id"] == rider_dispatch_request.pk
    assert detail["state"] == rider_dispatch_request_state_near_pickup.delivery_state
    assert detail["cancel_reason"] == ""


@pytest.mark.django_db(transaction=True)
def test_dispatch_requests_detail_cancelled(
    rider_dispatch_request, rider_dispatch_request_state_cancelled, mock_jwt_token
):
    # Given: 배차정보 및 상태기록이 있고

    # When: 배차 정보 조회 시,
    client = Client()
    response = client.get(
        reverse("ninja:mock_rider_app_dispatch_requests_detail") + f"?id={rider_dispatch_request.pk}",
        content_type="application/json",
        **{"HTTP_AUTHORIZATION": f"Bearer {mock_jwt_token}"},
    )
    # Then: 200 성공 응답, 배열이 반환되고
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert isinstance(data, list)

    # Then: 올바른 값이 포함되어 있고, 배차정보 및 상태가 반환된다
    detail = data[0]
    assert detail["dispatch_request_id"] == rider_dispatch_request.pk
    assert detail["state"] == rider_dispatch_request_state_cancelled.delivery_state
    assert detail["cancel_reason"] == CUSTOMER_ISSUE


@pytest.mark.django_db(transaction=True)
def test_retrieve_rider_dispatch_acceptance_rate(
    rider_dispatch_response, dummy_rider_dispatch_acceptance_rate, mock_jwt_token
):
    # Given: 라이더가 총 배차 1회 중 1회 수락 하였을 때,
    # When: 라이더 배차 수락률 조회 API를 호출 하였을 때
    client = Client()
    response = client.get(
        reverse("ninja:retrieve_rider_dispatch_acceptance_rate"),
        **{"HTTP_AUTHORIZATION": f"Bearer {mock_jwt_token}"},
    )

    # Then: 200 OK를 return 해야하고,
    assert response.status_code == HTTPStatus.OK
    # And: 라이더 배차 수락률이 일치해야한다.
    assert response.json() == dummy_rider_dispatch_acceptance_rate


@pytest.mark.django_db(transaction=True)
def test_retrieve_rider_mypage(
    rider_contract_type,
    mock_jwt_token,
    dummy_rider_profile,
    dummy_rider_dispatch_acceptance_rate,
    dummy_rider_working_report,
):
    # Given: 라이더가 총 배차 1회 중 1회 수락 하였을 때,
    # When: 라이더 마이페이지 정보 조회 API를 호출 하였을 때
    client = Client()
    response = client.get(
        reverse("ninja:retrieve_rider_mypage"),
        **{"HTTP_AUTHORIZATION": f"Bearer {mock_jwt_token}"},
    )

    # Then: 200 OK를 return 해야하고,
    assert response.status_code == HTTPStatus.OK
    # And: 라이더 마이페이지 정보가 일치해야한다.
    assert response.json() == dummy_rider_profile | dummy_rider_dispatch_acceptance_rate | dummy_rider_working_report


@pytest.mark.django_db(transaction=True)
def test_rider_mypage_return_when_search_data_does_not_exist(dummy_rider_profile, mock_jwt_token):
    # Given: 라이더 근무 내역이 없고,
    # When: 라이더 마이페이지 정보 조회 API를 호출 하였을 때
    client = Client()
    response = client.get(
        reverse("ninja:retrieve_rider_mypage"),
        **{"HTTP_AUTHORIZATION": f"Bearer {mock_jwt_token}"},
    )

    # Then: 200 OK를 return 해야하고,
    assert response.status_code == HTTPStatus.OK
    # And: 라이더 프로필 정보와 오늘의 내역 기본 설정 값을 제공해야한다.
    assert response.json() == dummy_rider_profile | {
        "total_delivery_count": 0,
        "total_commission": 0,
        "acceptance_rate": 0,
    }


@pytest.mark.django_db(transaction=True)
def test_retrieve_rider_service_agreements(rider_profile, rider_service_agreements, mock_jwt_token):
    # Given: 라이더가 서비스 이용약관에 동의한 경우
    # When: 서비스 이용약관 조회 API를 호출 하였을 때
    client = Client()
    response = client.get(
        reverse("ninja:rider_service_agreements"),
        HTTP_AUTHORIZATION=f"Bearer {mock_jwt_token}",
    )

    # Then: 200 OK를 return 해야하고,
    assert response.status_code == HTTPStatus.OK

    # And: 이용약관에 대한 응답이 반환되어야 한다.
    data = response.json()
    assert data["personal_information"] is True
    assert data["location_based_service"] is True
    assert data["promotion_receivable"] is False
    assert data["night_promotion_receivable"] is False


@pytest.mark.django_db(transaction=True)
def test_retrieve_rider_service_agreements_return_not_found_when_missing_required_agreements(
    rider_profile, mock_jwt_token
):
    # Given: 라이더가 서비스 이용약관에 동의하지 않은 경우
    # When: 서비스 이용약관 조회 API를 호출 하였을 때
    client = Client()
    response = client.get(
        reverse("ninja:rider_service_agreements"),
        HTTP_AUTHORIZATION=f"Bearer {mock_jwt_token}",
    )

    # Then: 200 OK를 return 해야하고,
    assert response.status_code == HTTPStatus.NOT_FOUND

    # And: 이용약관에 대한 응답이 반환되어야 한다.
    data = response.json()
    assert data["message"] == MSG_AGREEMENT_NOT_SUBMITTED


@pytest.mark.django_db(transaction=True)
def test_create_rider_service_agreements(rider_profile, mock_jwt_token):
    # Given: 라이더의 서비스 이용약관 정보가 없고
    assert not RiderServiceAgreement.objects.filter(rider_id=rider_profile.pk)

    # When: 서비스 이용약관 저장 API를 호출 하였을 때
    input_body = {
        "personal_information": True,
        "location_based_service": True,
        "promotion_receivable": False,
        "night_promotion_receivable": False,
    }

    client = Client()
    current_time = timezone.localtime()
    with freeze_time(current_time):
        response = client.post(
            reverse("ninja:rider_service_agreements"),
            data=input_body,
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {mock_jwt_token}",
        )

        # Then: 200 OK를 return 해야하고,
        assert response.status_code == HTTPStatus.OK

        # And: 이용약관 저장 시간이 반환된다.
        data = response.json()
        assert data["personal_information"] is True
        assert data["location_based_service"] is True
        assert data["promotion_receivable"] is False
        assert data["night_promotion_receivable"] is False
        assert data["agreement_saved_time"] == current_time.strftime("%Y-%m-%d %H:%M:%S")


@pytest.mark.django_db(transaction=True)
def test_create_rider_service_agreements_return_error_when_required_is_false(rider_profile, mock_jwt_token):
    # Given: 라이더의 서비스 이용약관 정보가 없고
    assert not RiderServiceAgreement.objects.filter(rider_id=rider_profile.pk)

    # When: 서비스 이용약관 저장 API를 호출 하였을 때
    input_body = {
        "personal_information": False,
        "location_based_service": True,
        "promotion_receivable": False,
        "night_promotion_receivable": False,
    }

    client = Client()
    current_time = timezone.localtime()
    with freeze_time(current_time):
        response = client.post(
            reverse("ninja:rider_service_agreements"),
            data=input_body,
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {mock_jwt_token}",
        )

        # Then: 400를 return 해야하고,
        assert response.status_code == HTTPStatus.BAD_REQUEST

        # And: 에러메시지가 반환된다.
        data = response.json()
        assert data["message"] == MSG_MUST_AGREE_REQUIRED_AGREEMENTS


@pytest.mark.django_db(transaction=True)
def test_create_rider_service_agreements_return_error_when_exist(
    rider_profile, rider_service_agreements, mock_jwt_token
):
    # Given: 라이더의 서비스 이용약관 정보가 있는 경우
    assert RiderServiceAgreement.objects.filter(rider_id=rider_profile.pk)

    # When: 서비스 이용약관 저장 API를 호출 하였을 때
    input_body = {
        "personal_information": True,
        "location_based_service": True,
        "promotion_receivable": False,
        "night_promotion_receivable": False,
    }

    client = Client()
    current_time = timezone.localtime()
    with freeze_time(current_time):
        response = client.post(
            reverse("ninja:rider_service_agreements"),
            data=input_body,
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {mock_jwt_token}",
        )

        # Then: 400를 return 해야하고,
        assert response.status_code == HTTPStatus.BAD_REQUEST

        # And: 에러메시지가 반환된다.
        data = response.json()
        assert data["message"] == MSG_AGREEMENT_ALREADY_SUBMITTED


@pytest.mark.django_db(transaction=True)
def test_partial_update_rider_service_agreements(rider_profile, rider_service_agreements, mock_jwt_token):
    # Given: 라이더의 서비스 이용약관 정보가 있고
    agreement = RiderServiceAgreement.objects.get(
        rider_id=rider_profile.pk,
        agreement_type=ServiceAgreementType.PROMOTION_RECEIVABLE,
    )
    assert agreement.agreed is False

    # When: 서비스 이용약관 저장 API를 호출 하였을 때
    input_body = {"promotion_receivable": True}

    client = Client()
    current_time = timezone.localtime()
    with freeze_time(current_time):
        response = client.patch(
            reverse("ninja:rider_service_agreements"),
            data=input_body,
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {mock_jwt_token}",
        )

        # Then: 200 OK를 return 해야하고,
        assert response.status_code == HTTPStatus.OK

        # And: 이용약관 저장 시간이 반환된다.
        data = response.json()
        assert data["promotion_receivable"] is True
        assert data["agreement_saved_time"] == current_time.strftime("%Y-%m-%d %H:%M:%S")

    agreement.refresh_from_db()
    assert agreement.agreed is True


@pytest.mark.django_db(transaction=True)
def test_partial_update_rider_service_agreements_return_when_attempt_to_update_required_agreement(
    rider_profile, rider_service_agreements, mock_jwt_token
):
    # Given: 라이더의 서비스 이용약관 정보가 있고, 필수 이용약관 동의한 경우
    agreement = RiderServiceAgreement.objects.get(
        rider_id=rider_profile.pk,
        agreement_type=ServiceAgreementType.PERSONAL_INFORMATION,
    )
    assert agreement.agreed is True

    # And: 수정 가능한 이용약관 외에 정보를 입력한 경우 (필수 이용약관 거절)
    invalid_body = {"personal_information": False}

    # When: 서비스 이용약관 저장 API를 호출 하였을 때
    client = Client()
    current_time = timezone.localtime()
    with freeze_time(current_time):
        response = client.patch(
            reverse("ninja:rider_service_agreements"),
            data=invalid_body,
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {mock_jwt_token}",
        )

        # Then: 422 UNPROCESSABLE_ENTITY를 return 해야하고,
        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
        data = response.json()
        assert data["message"] == "요청을 처리할 수 없습니다."

    # And: 값은 변경되지 않는다.
    agreement.refresh_from_db()
    assert agreement.agreed is True


@pytest.mark.django_db(transaction=True)
def test_partial_update_rider_service_agreements_return_when_invalid_request(
    rider_profile, rider_service_agreements, mock_jwt_token
):
    # Given: 라이더의 서비스 이용약관 정보가 있고, 필수 이용약관 동의한 경우
    # And: 수정 가능한 이용약관 외에 정보를 입력한 경우 (이상한 값)
    invalid_body = {"morning_promotion_receivable": False}

    # When: 서비스 이용약관 저장 API를 호출 하였을 때
    client = Client()
    current_time = timezone.localtime()
    with freeze_time(current_time):
        response = client.patch(
            reverse("ninja:rider_service_agreements"),
            data=invalid_body,
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {mock_jwt_token}",
        )

        # Then: 422 UNPROCESSABLE_ENTITY를 return 해야한다
        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
        data = response.json()
        assert data["message"] == "요청을 처리할 수 없습니다."


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    "dispatch_delivery_state",
    (
        DeliveryState.DISPATCHED,
        DeliveryState.NOTIFIED,
        DeliveryState.ACCEPTED,
        DeliveryState.NEAR_PICKUP,
        DeliveryState.PICK_UP,
        DeliveryState.LEFT_PICKUP,
        DeliveryState.NEAR_DROPOFF,
    ),
)
def test_retreive_rider_state_must_include_in_progress_deliveries(
    rider_profile, rider_dispatch_request, rider_state, mock_jwt_token, dispatch_delivery_state
):
    # Given: 라이더가 진행 중인 배차가 있는 경우
    delivery_state_history = rider_dispatch_request.riderdeliverystatehistory_set.order_by("-created_at").first()
    delivery_state_history.state = dispatch_delivery_state
    delivery_state_history.save()

    # When: 라이더 상태 조회 API 호출 시
    client = Client()
    response = client.get(
        reverse("ninja:rider_app_rider_state"),
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {mock_jwt_token}",
    )

    # Then: 200 OK 를 return 해야한다
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    # And: 현재 상태를 반환하고
    assert data["state"] == rider_state.state
    # And: 현재 배달 중이 배차번호를 반환한다
    assert data["current_deliveries"] == str(rider_dispatch_request.pk)


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    "dispatch_delivery_state",
    (
        DeliveryState.DECLINED,
        DeliveryState.IGNORED,
        DeliveryState.COMPLETED,
        DeliveryState.CANCELLED,
    ),
)
def test_retreive_rider_state_must_not_include_not_in_progress_deliveries(
    rider_profile, rider_dispatch_request, rider_state, mock_jwt_token, dispatch_delivery_state
):
    # Given: 라이더가 진행 중인 배차가 없는 경우
    delivery_state_history = rider_dispatch_request.riderdeliverystatehistory_set.order_by("-created_at").first()
    delivery_state_history.delivery_state = dispatch_delivery_state
    delivery_state_history.save()

    # When: 라이더 상태 조회 API 호출 시
    client = Client()
    response = client.get(
        reverse("ninja:rider_app_rider_state"),
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {mock_jwt_token}",
    )

    # Then: 200 OK 를 return 해야한다
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    # And: 현재 상태를 반환하고
    assert data["state"] == rider_state.state
    # And: 현재 배달 중이 배차번호를 반환한다
    assert data["current_deliveries"] == ""
