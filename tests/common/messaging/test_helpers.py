from unittest.mock import patch

from ras.common.messaging import SNSMessageForPublish, publish_message


@patch("ras.common.messaging.helpers.sns_client.publish")
def test_publish_message(mock_sns_publish):
    # Given: SNSMessageForPublish Schema로 정의된 message가 있고
    sns_message = SNSMessageForPublish(topic_arn="test-topic-arn", message='{"test-message": 123}')
    # And: sns publish 호출시 True를 반환하는 경우
    mock_sns_publish.return_value = True

    # When: message를 publish 하면
    result = publish_message(sns_message)

    # Then: 예상한 mock 결과가 반환되고,
    assert result is True
    # And: publish 요청인자는 미리 정의한 message 값들과 일치한다.
    mock_sns_publish.assert_called_once_with(TopicArn="test-topic-arn", Message='{"test-message": 123}')
