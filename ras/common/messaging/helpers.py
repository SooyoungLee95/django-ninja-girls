import boto3
from django.conf import settings

from .schema import SNSMessage

sns_client = boto3.client(
    "sns",
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_REGION,
    endpoint_url=settings.AWS_SNS_ENDPOINT_URL,
)


def publish_message(sns_message: SNSMessage):
    return sns_client.publish(**sns_message.dict(exclude_none=True, exclude_unset=True))
