import json
from http import HTTPStatus

from ninja.router import Router

from ras.common.messaging.publishers import publish_message
from ras.common.messaging.schema import SNSMessageForPublish
from ras.debug.schemas import DebugEventTriggerMessage, Event, event_to_topic
from ras.rideryo.models import RiderServiceAgreement

debug_router = Router()


@debug_router.post("/trigger-event")
def debug_trigger_event(request, event: Event, body: DebugEventTriggerMessage):
    publish_message(SNSMessageForPublish(topic_arn=event_to_topic[event], message=json.dumps(body.message)))
    return HTTPStatus.OK


@debug_router.post("/reset-service-agreements")
def debug_reset_service_agreements(request):
    rider_id = request.auth.pk
    return HTTPStatus.OK, RiderServiceAgreement.objects.filter(rider_id=rider_id).delete()
