from http import HTTPStatus
from unittest.mock import patch

import pytest
from django.db.utils import IntegrityError
from django.test import Client
from django.urls import reverse

from ras.common.integration.services.jungleworks.schemas import JungleworksResponseBody
from ras.rider_app.schemas import RiderAvailability, RiderDispatchResponse


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("jungleworks_enabled", [(True,), (False,)])
@patch("ras.rider_app.views.should_connect_jungleworks")
def test_update_rider_availability(mock_use_jungleworks, jungleworks_enabled, rider_profile):
    def call_api():
        return client.put(
            reverse("ninja:rider_app_update_rider_availability"),
            data=input_body.dict(),
            content_type="application/json",
        )

    client = Client()
    input_body = RiderAvailability(rider_id=rider_profile.pk, is_available=True)

    if jungleworks_enabled:
        # Given: Jungleworks 기능이 활성화되고,
        mock_use_jungleworks.return_value = True
        # And: Jungleworks API에서 성공 응답을 반환하는 경우
        expected_jungleworks_response = JungleworksResponseBody(message="test-message", status=200, data={})

        # When: 라이더 업무 시작/종료 API 호출 시,
        with patch("ras.rider_app.helpers.on_off_duty") as mock_on_off_duty:
            mock_on_off_duty.return_value = expected_jungleworks_response
            response = call_api()

        # Then: Jungleworks 응답코드에 상응하는 응답코드가 반환되고,
        assert response.status_code == expected_jungleworks_response.relevant_http_status()

    else:
        # Given: Jungleworks 기능이 비활성화된 경우
        mock_use_jungleworks.return_value = False

        # When: 라이더 업무 시작/종료 API 호출 시,
        with patch("ras.rider_app.helpers.query_update_rider_availability") as mock_query_update:
            response = call_api()
            mock_query_update.assert_called_once()

        # Then: 200 응답코드가 반환되고,
        assert response.status_code == HTTPStatus.OK

    # And: Jungleworks 활성화 체크 함수 및 응답값이 올바른지 확인한다.
    mock_use_jungleworks.assert_called_once()
    assert response.json() == input_body.dict()


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("jungleworks_enabled", [(True,), (False,)])
@patch("ras.rider_app.views.should_connect_jungleworks")
def test_update_rider_availability_error(mock_use_jungleworks, jungleworks_enabled, rider_profile):
    def call_api():
        return client.put(
            reverse("ninja:rider_app_update_rider_availability"),
            data=input_body.dict(),
            content_type="application/json",
        )

    client = Client()
    input_body = RiderAvailability(rider_id=rider_profile.pk, is_available=True)

    if jungleworks_enabled:
        # Given: Jungleworks 기능이 활성화되고,
        mock_use_jungleworks.return_value = True
        # And: Jungleworks API에서 에러 응답을 반환하는 경우
        expected_jungleworks_response = JungleworksResponseBody(message="invalid", status=100, data={})

        # When: 라이더 업무 시작/종료 API 호출 시,
        with patch("ras.rider_app.helpers.on_off_duty") as mock_on_off_duty:
            mock_on_off_duty.return_value = expected_jungleworks_response
            response = call_api()

        # Then: Jungleworks 응답코드에 상응하는 응답코드가 반환되고,
        assert response.status_code == expected_jungleworks_response.relevant_http_status()
        # And: Jungleworks 활성화 체크 함수 및 응답값이 올바른지 확인한다.
        mock_use_jungleworks.assert_called_once()
        assert response.json() == {"errors": [{"name": "reason", "message": "invalid"}]}

    else:
        # Given: Jungleworks 기능이 비활성화된 경우
        mock_use_jungleworks.return_value = False

        # When: 라이더 업무 시작/종료 API 호출 시,
        with patch("ras.rider_app.helpers.query_update_rider_availability") as mock_query_update:
            # DB 조회시 에러 발생
            mock_query_update.side_effect = IntegrityError()
            response = call_api()

        # Then: 400 응답코드가 반환된다.
        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert response.json() == {"errors": [{"name": "reason", "message": "라이더를 식별할 수 없습니다."}]}


class TestRiderDispatchResponse:
    def _call_api_create_rider_dispatch_response(self, input_body):
        client = Client()

        return client.post(
            reverse("ninja:create_rider_dispatch_response"),
            data=input_body.dict(),
            content_type="application/json",
        )

    def _make_request_body(self, dispatch_request_id, response):
        return RiderDispatchResponse(dispatch_request_id=dispatch_request_id, response=response)

    @pytest.mark.django_db(transaction=True)
    @patch("ras.rider_app.views.should_connect_jungleworks")
    def test_create_rider_dispatch_when_jw_enabled(self, mock_use_jungleworks, rider_dispatch_request):
        # Given: Jungleworks 기능이 활성화되고,
        mock_use_jungleworks.return_value = True
        # And: Jungleworks API에서 성공 응답을 반환하는 경우
        expected_jungleworks_response = JungleworksResponseBody(message="test-message", status=200, data={})

        # When: 라이더 배차 수락/거질/무시 API 호출 시,
        with patch("ras.rider_app.helpers.update_task_status") as mock_update_task_status:
            mock_update_task_status.return_value = expected_jungleworks_response
            input_body = self._make_request_body(rider_dispatch_request.id, "ACCEPTED")
            response = self._call_api_create_rider_dispatch_response(input_body)

        # Then: Jungleworks 응답코드에 상응하는 응답코드가 반환된다.
        assert response.status_code == expected_jungleworks_response.relevant_http_status()

        # And: Jungleworks 활성화 체크 함수 및 응답값이 올바른지 확인한다.
        mock_use_jungleworks.assert_called_once()
        assert response.json() == input_body.dict()

    @pytest.mark.django_db(transaction=True)
    @patch("ras.rider_app.views.should_connect_jungleworks")
    def test_create_rider_dispatch_when_jw_not_enabled(self, mock_use_jungleworks, rider_dispatch_request):
        # Given: Jungleworks 기능이 비활성화된 경우
        mock_use_jungleworks.return_value = False

        # When: 라이더 배차 수락/거절/무시 API 호출 시,
        with patch("ras.rider_app.helpers.query_create_rider_dispatch_response") as mock_query_create:
            input_body = self._make_request_body(rider_dispatch_request.id, "ACCEPTED")
            response = self._call_api_create_rider_dispatch_response(input_body)
            mock_query_create.assert_called_once()

        # Then: 200 응답코드가 반환되고,
        assert response.status_code == HTTPStatus.OK

        # And: Jungleworks 활성화 체크 함수 및 응답값이 올바른지 확인한다.
        mock_use_jungleworks.assert_called_once()
        assert response.json() == input_body.dict()

    @pytest.mark.django_db(transaction=True)
    @patch("ras.rider_app.views.should_connect_jungleworks")
    def test_update_rider_dispatch_error_when_jw_enabled(self, mock_use_jungleworks, rider_dispatch_request):
        # Given: Jungleworks 기능이 활성화되고,
        mock_use_jungleworks.return_value = True
        # And: Jungleworks API에서 에러 응답을 반환하는 경우
        expected_jungleworks_response = JungleworksResponseBody(message="invalid", status=100, data={})

        # When: 라이더 배차 수락/거질/무시 API 호출 시,
        with patch("ras.rider_app.helpers.update_task_status") as mock_update_task_status:
            mock_update_task_status.return_value = expected_jungleworks_response
            input_body = self._make_request_body(rider_dispatch_request.id, "ACCEPTED")
            response = self._call_api_create_rider_dispatch_response(input_body)

        # Then: Jungleworks 응답코드에 상응하는 응답코드가 반환되고,
        assert response.status_code == expected_jungleworks_response.relevant_http_status()
        # And: Jungleworks 활성화 체크 함수 및 응답값이 올바른지 확인한다.
        mock_use_jungleworks.assert_called_once()
        assert response.json() == {"errors": [{"name": "reason", "message": "invalid"}]}

    @pytest.mark.django_db(transaction=True)
    @patch("ras.rider_app.views.should_connect_jungleworks")
    def test_update_rider_dispatch_error_when_jw_not_enabled(self, mock_use_jungleworks, rider_dispatch_request):
        # Given: Jungleworks 기능이 비활성화된 경우
        mock_use_jungleworks.return_value = False

        # When: 라이더 업무 시작/종료 API 호출 시,
        with patch("ras.rider_app.helpers.query_create_rider_dispatch_response") as mock_query_create:
            # DB 조회시 에러 발생
            mock_query_create.side_effect = IntegrityError()
            input_body = self._make_request_body(rider_dispatch_request.id, "ACCEPTED")
            response = self._call_api_create_rider_dispatch_response(input_body)

        # Then: 400 응답코드가 반환된다.
        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert response.json() == {"errors": [{"name": "reason", "message": "유효한 ID 값이 아닙니다."}]}

    @pytest.mark.django_db(transaction=True)
    @patch("ras.rider_app.views.should_connect_jungleworks")
    def test_create_rider_dispatch_notified_when_jw_enabled(self, mock_use_jungleworks, rider_dispatch_request):
        # Given: Jungleworks 기능이 활성화되고,
        mock_use_jungleworks.return_value = True
        # And: Jungleworks API에서 성공 응답을 반환하는 경우
        expected_jungleworks_response = JungleworksResponseBody(message="test-message", status=200, data={})

        # When: 라이더 배차 수락/거질/무시 API 호출 시,
        with patch("ras.rider_app.helpers.update_task_status") as mock_update_task_status:
            mock_update_task_status.return_value = expected_jungleworks_response
            input_body = self._make_request_body(rider_dispatch_request.id, "NOTIFIED")
            response = self._call_api_create_rider_dispatch_response(input_body)

        # Then: Jungleworks update_task_status API가 호출되지 않고,
        assert mock_update_task_status.call_count == 0
        # AND: Jungleworks 응답코드에 상응하는 응답코드가 반환된다.
        assert response.status_code == expected_jungleworks_response.relevant_http_status()

        # And: Jungleworks 활성화 체크 함수 및 응답값이 올바른지 확인한다.
        mock_use_jungleworks.assert_called_once()
        assert response.json() == input_body.dict()

    @pytest.mark.django_db(transaction=True)
    @patch("ras.rider_app.views.should_connect_jungleworks")
    def test_create_rider_dispatch_notified_when_jw_not_enabled(self, mock_use_jungleworks, rider_dispatch_request):
        # Given: Jungleworks 기능이 비활성화된 경우
        mock_use_jungleworks.return_value = False

        # When: 라이더 배차 수락/거절/무시 API 호출 시,
        with patch("ras.rider_app.helpers.query_create_rider_dispatch_response") as mock_query_create:
            input_body = self._make_request_body(rider_dispatch_request.id, "NOTIFIED")
            response = self._call_api_create_rider_dispatch_response(input_body)
            mock_query_create.assert_called_once()

        # Then: 200 응답코드가 반환되고,
        assert response.status_code == HTTPStatus.OK

        # And: Jungleworks 활성화 체크 함수 및 응답값이 올바른지 확인한다.
        mock_use_jungleworks.assert_called_once()
        assert response.json() == input_body.dict()
