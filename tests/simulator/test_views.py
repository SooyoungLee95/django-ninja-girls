from http import HTTPStatus
from unittest.mock import patch

import pytest
from django.test import Client
from django.urls import reverse

from ras.rider.schemas import RiderState
from ras.simulator.schemas import RiderShiftSimulatedAction, RiderSimulatedAction


@patch("ras.simulator.helpers.publish_message")
def test_trigger_rider_location(mock_publish_message):
    # Given: SNS Publish가 성공하는 상황을 가정하고
    expected_publish_message_return_value = {"status": 200}
    mock_publish_message.return_value = expected_publish_message_return_value

    # When: location 변경 트리거가 발생하는 경우
    expected_rider_id = 1
    expected_rider_lat = 37.04921
    expected_rider_lng = 127.12345
    expected_zone_id = 1
    trigger_payload = {
        "rider_id": expected_rider_id,
        "location": {
            "lat": expected_rider_lat,
            "lng": expected_rider_lng,
        },
    }
    client = Client()
    response = client.post(
        reverse("ninja:simulator_rider_location_trigger"),
        data=trigger_payload,
        content_type="application/json",
    )

    # Then: 성공응답을 반환하고
    assert response.status_code == HTTPStatus.OK

    # And: SNS Publish가 호출되고
    mock_publish_message.assert_called_once()

    # And: 게시된 message 및 publish 응답이 반환된다
    data = response.json()
    assert data["message"]["event_id"].startswith("ras:")
    assert data["message"]["event_type"] == "update"
    assert data["message"]["event_name"] == "rider-location-update"
    assert data["message"]["id"] == expected_rider_id
    assert data["message"]["zone_id"] == expected_zone_id
    assert data["message"]["current_location"]["lat"] == expected_rider_lat
    assert data["message"]["current_location"]["lng"] == expected_rider_lng
    assert data["message"]["state"] == "in_transit"
    assert data["response"] == expected_publish_message_return_value


@pytest.mark.parametrize(
    "expected_state, rider_action",
    [
        (RiderState.AVAILABLE, RiderSimulatedAction.LOGIN),
        (RiderState.NOT_WORKING, RiderSimulatedAction.LOGOUT),
        (RiderState.IN_TRANSIT, RiderSimulatedAction.ACCEPT_DELIVERY),
        (RiderState.AVAILABLE, RiderSimulatedAction.DECLINE_DELIVERY),
        (RiderState.AVAILABLE, RiderSimulatedAction.COMPLETE_DELIVERY),
        (RiderState.BREAK, RiderSimulatedAction.TAKE_A_BREAK),
    ],
)
def test_trigger_rider_status(expected_state, rider_action):
    # When: rider action 트리거가 발생하는 경우
    expected_rider_id = 1
    expected_rider_lat = 37.04921
    expected_rider_lng = 127.12345
    expected_zone_id = 1
    trigger_payload = {
        "rider_id": expected_rider_id,
        "action": rider_action,
        "location": {
            "lat": expected_rider_lat,
            "lng": expected_rider_lng,
        },
    }
    client = Client()
    with patch("ras.simulator.helpers.publish_message") as mock_publish_message:
        # Given: SNS Publish가 성공하는 상황을 가정하고
        expected_publish_message_return_value = {"status": 200}
        mock_publish_message.return_value = expected_publish_message_return_value

        response = client.post(
            reverse("ninja:simulator_rider_status_trigger"),
            data=trigger_payload,
            content_type="application/json",
        )

        # Then: SNS Publish가 호출되고
        mock_publish_message.assert_called_once()

    # And: 성공응답을 반환하고
    assert response.status_code == HTTPStatus.OK

    # And: 게시된 message 및 publish 응답이 반환된다
    data = response.json()
    assert data["message"]["event_id"].startswith("ras:")
    assert data["message"]["event_type"] == "update"
    assert data["message"]["event_name"] == f"rider-{rider_action.value}"
    assert data["message"]["id"] == expected_rider_id
    assert data["message"]["zone_id"] == expected_zone_id
    assert data["message"]["current_location"]["lat"] == expected_rider_lat
    assert data["message"]["current_location"]["lng"] == expected_rider_lng
    assert data["message"]["state"] == expected_state.value
    assert data["response"] == expected_publish_message_return_value


@pytest.mark.parametrize(
    "expected_state, shift_action",
    [
        (RiderState.AVAILABLE, RiderShiftSimulatedAction.SHIFT_START),
        (RiderState.NOT_WORKING, RiderShiftSimulatedAction.SHIFT_END),
    ],
)
def test_trigger_rider_shift(expected_state, shift_action):
    # When: shift action 트리거가 발생하는 경우
    expected_rider_id = 1
    expected_rider_lat = 37.04921
    expected_rider_lng = 127.12345
    expected_zone_id = 1
    trigger_payload = {
        "rider_id": expected_rider_id,
        "action": shift_action.value,
        "start_at": "2021-05-18T10:00:00.000000",
        "end_at": "2021-05-18T10:15:00.000000",
        "location": {
            "lat": expected_rider_lat,
            "lng": expected_rider_lng,
        },
    }
    client = Client()
    with patch("ras.simulator.helpers.publish_message") as mock_publish_message:
        # Given: SNS Publish가 성공하는 상황을 가정하고
        expected_publish_message_return_value = {"status": 200}
        mock_publish_message.return_value = expected_publish_message_return_value

        response = client.post(
            reverse("ninja:simulator_rider_shift_trigger"),
            data=trigger_payload,
            content_type="application/json",
        )

        # Then: SNS Publish가 호출되고
        mock_publish_message.assert_called_once()

    # And: 성공응답을 반환하고
    assert response.status_code == HTTPStatus.OK

    # And: 게시된 message 및 publish 응답이 반환된다
    data = response.json()
    assert data["message"]["event_id"].startswith("ras:")
    assert data["message"]["event_type"] == "update"
    assert data["message"]["event_name"] == f"rider-{shift_action.value}"
    assert data["message"]["id"] == expected_rider_id
    assert data["message"]["zone_id"] == expected_zone_id
    assert data["message"]["current_location"]["lat"] == expected_rider_lat
    assert data["message"]["current_location"]["lng"] == expected_rider_lng
    assert data["message"]["state"] == expected_state.value
    assert data["response"] == expected_publish_message_return_value
