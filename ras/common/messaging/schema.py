from typing import Any, Dict, Optional

import orjson
from ninja import Schema
from pydantic import Field


# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sns.html#SNS.Client.publish
class SNSMessageForPublish(Schema):
    TopicArn: str = Field(alias="topic_arn")
    Message: str = Field(alias="message")
    TargetArn: Optional[str] = Field(alias="target_arn")
    PhoneNumber: Optional[str] = Field(alias="phone_number")
    Subject: Optional[str] = Field(alias="subject")
    MessageStructure: Optional[str] = Field(alias="message_structure")
    MessageAttributes: Optional[Dict[str, Dict[str, Any]]] = Field(alias="message_attributes")
    MessageDeduplicationId: Optional[str] = Field(alias="message_deduplication_id")
    MessageGroupId: Optional[str] = Field(alias="message_group_id")


class SNSMessageForSubscribe(Schema):
    type: str = Field(alias="Type")
    message_id: str = Field(alias="MessageId")
    topic_arn: str = Field(alias="TopicArn")
    message_: str = Field(alias="Message")
    timestamp: str = Field(alias="Timestamp")
    signature_version: str = Field(alias="SignatureVersion")
    signature: str = Field(alias="Signature")
    signing_cert_url: str = Field(alias="SigningCertURL")
    subscribe_url: Optional[str] = Field(alias="SubscribeURL")
    unsubscribe_url: Optional[str] = Field(alias="UnsubscribeURL")
    token: Optional[str] = Field(alias="Token")

    @property
    def message(self) -> dict[str, Any]:
        return orjson.loads(self.message_)
