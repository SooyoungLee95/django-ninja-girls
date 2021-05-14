from typing import Any, Dict, Optional

from ninja import Schema
from pydantic import Field


# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sns.html#SNS.Client.publish
class SNSMessage(Schema):
    TopicArn: str = Field(alias="topic_arn")
    Message: str = Field(alias="message")
    TargetArn: Optional[str] = Field(alias="target_arn")
    PhoneNumber: Optional[str] = Field(alias="phone_number")
    Subject: Optional[str] = Field(alias="subject")
    MessageStructure: Optional[str] = Field(alias="message_structure")
    MessageAttributes: Optional[Dict[str, Dict[str, Any]]] = Field(alias="message_attributes")
    MessageDeduplicationId: Optional[str] = Field(alias="message_deduplication_id")
    MessageGroupId: Optional[str] = Field(alias="message_group_id")
