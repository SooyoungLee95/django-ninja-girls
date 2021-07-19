#!bin/bash

ENDPOINT_BASE_URL='http://host.docker.internal:8000/api'
echo "notification-endpoint-base-url: $ENDPOINT_BASE_URL"

awslocal sns subscribe --topic-arn "arn:aws:sns:us-east-1:000000000000:order" --protocol http --notification-endpoint $ENDPOINT_BASE_URL/rider-app/sns/subs/order
