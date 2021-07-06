from unittest.mock import Mock, patch

import pytest

from ras.common.fcm import FCMSender


@pytest.fixture
@patch("ras.common.fcm.credentials.Certificate", Mock())
@patch("ras.common.fcm.firebase_admin", Mock())
def fcm_sender():
    fcm = FCMSender()
    return fcm


@pytest.fixture
def fcm_sample():
    data = {
        "title": "test_title",
        "body": "test_body",
        "registration_token": "dFrn2w0HPNT",
        "rider_id": "123",
        "dispatch_id": "456",
    }
    return data


class TestFCMSender:
    @patch("ras.common.fcm.messaging.send")
    def test_should_send_fcm(self, mock_send, fcm_sender, fcm_sample):
        # Given: FCM Sender & Sample data
        # When: FCM 전송
        result = fcm_sender.send(fcm_sample)

        # Then: 발송 성공
        message = mock_send.call_args.args[0]
        mock_send.assert_called_once()
        assert message.apns.payload.aps.alert.title == "test_title"
        assert message.apns.payload.aps.alert.body == "test_body"
        assert message.apns.payload.custom_data["data"] == fcm_sample
        assert message.android.notification.title == "test_title"
        assert message.android.notification.body == "test_body"
        assert message.android.data == fcm_sample
        assert message.token == "dFrn2w0HPNT"
        assert result == {"success": True}
