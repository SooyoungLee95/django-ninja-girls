import logging
from typing import Optional
from urllib.parse import urljoin

import httpx
from django.conf import settings

from ras.rider_app.schemas import RiderAvailability, RiderDispatchResponse
from ras.rideryo.enums import RiderResponse

from ...connection import AsyncExternalClient
from .schemas import (
    JungleworksRequestBody,
    JungleworksResponseBody,
    OnOffDutyRequestBody,
    TaskStatusRequestBody,
)

ON_OFF_DUTY = "on_off_duty"
UPDATE_TASK_STATUS = "update_task_status"
JUNGLEWORKS_PATHS = {
    ON_OFF_DUTY: "/v2/change_fleet_availability",
    UPDATE_TASK_STATUS: "/v2/update_task_status",
}
JungleworksTaskStatus = {
    RiderResponse.ACCEPTED: "7",
    RiderResponse.DECLINED: "8",
    RiderResponse.IGNORED: "8",
}

logger = logging.getLogger(__name__)


async def call_jungleworks_api(
    *, path_namespace: str, body: JungleworksRequestBody, method="POST"
) -> Optional[JungleworksResponseBody]:
    url = urljoin(settings.JUNGLEWORKS_BASE_URL, JUNGLEWORKS_PATHS[path_namespace])
    async with AsyncExternalClient() as client:
        try:
            response = await client.request(method, url, json=body.dict())
        except httpx.RequestError as e:
            logger.error(f"[Jungleworks] {e!r}")
            return None
        else:
            return JungleworksResponseBody(**response.json())


async def on_off_duty(rider_availability: RiderAvailability):
    request_body = OnOffDutyRequestBody(
        fleet_ids=[rider_availability.rider_id],
        is_available=rider_availability.is_available,
    )
    return await call_jungleworks_api(path_namespace=ON_OFF_DUTY, body=request_body)


async def update_task_status(task_status: RiderDispatchResponse):
    request_body = TaskStatusRequestBody(
        job_id=task_status.dispatch_request_id,
        job_status=JungleworksTaskStatus[task_status.response],
    )
    return await call_jungleworks_api(path_namespace=UPDATE_TASK_STATUS, body=request_body)


def should_connect_jungleworks(request):
    return settings.JUNGLEWORKS_ENABLE or (settings.DEBUG and request.META["QUERY_STRING"].startswith("JW"))
