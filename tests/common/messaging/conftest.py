import pytest


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
