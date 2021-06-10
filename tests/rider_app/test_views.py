from http import HTTPStatus
from unittest.mock import patch

import pytest
from django.test import Client
from django.urls import reverse

from ras.common.integration.services.jungleworks.schemas import JungleworksResponseBody
from ras.rider_app.schemas import RiderAvailability


@pytest.mark.parametrize("jungleworks_enabled", [(True,), (False,)])
@patch("ras.rider_app.views.should_connect_jungleworks")
def test_update_rider_availability(mock_use_jungleworks, jungleworks_enabled):
    def call_api():
        return client.put(
            reverse("ninja:rider_app_update_rider_availability"),
            data=input_body.dict(),
            content_type="application/json",
        )

    client = Client()
    input_body = RiderAvailability(rider_id=1, is_available=True)

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
        response = call_api()

        # Then: 200 응답코드가 반환되고,
        assert response.status_code == HTTPStatus.OK

    # And: Jungleworks 활성화 체크 함수 및 응답값이 올바른지 확인한다.
    mock_use_jungleworks.assert_called_once()
    assert response.json() == input_body.dict()


@pytest.mark.parametrize("jungleworks_enabled", [(True,), (False,)])
@patch("ras.rider_app.views.should_connect_jungleworks")
def test_update_rider_availability_error(mock_use_jungleworks, jungleworks_enabled):
    def call_api():
        return client.put(
            reverse("ninja:rider_app_update_rider_availability"),
            data=input_body.dict(),
            content_type="application/json",
        )

    client = Client()
    input_body = RiderAvailability(rider_id=1, is_available=True)

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
        # TODO: 모델링 코드 반영 이후 테스트 추가
        pass
