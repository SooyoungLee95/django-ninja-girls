import logging
from typing import Optional
from urllib.parse import urljoin

import httpx
from django.conf import settings

from ras.rider_app.queries import query_get_dispatch_jungleworks_tasks
from ras.rider_app.schemas import (
    RiderAvailability,
    RiderDeliveryState,
    RiderDispatchResponse,
)
from ras.rideryo.enums import DeliveryState, JungleworksTaskStatus, RiderResponse

from ...connection import AsyncExternalClient
from .schemas import (
    JungleworksRequestBody,
    JungleworksResponseBody,
    OnOffDutyRequestBody,
    RetrieveDeliveryTaskIdRequestBody,
    TaskStatusRequestBody,
)

ON_OFF_DUTY = "on_off_duty"
UPDATE_TASK_STATUS = "update_task_status"
RETRIEVE_DELIVERY_TASK_ID = "get_related_tasks"

JUNGLEWORKS_PATHS = {
    ON_OFF_DUTY: "/v2/change_fleet_availability",
    UPDATE_TASK_STATUS: "/v2/update_task_status",
    RETRIEVE_DELIVERY_TASK_ID: "/v2/get_related_tasks",
}
response_to_junglework_status = {
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


async def on_off_duty(rider_id, availability: RiderAvailability):
    request_body = OnOffDutyRequestBody(
        fleet_ids=[rider_id],
        is_available=availability.is_available,
    )
    return await call_jungleworks_api(path_namespace=ON_OFF_DUTY, body=request_body)


async def _update_task_status(task_id, task_status):
    request_body = TaskStatusRequestBody(job_id=task_id, job_status=task_status)
    return await call_jungleworks_api(path_namespace=UPDATE_TASK_STATUS, body=request_body)


async def update_task_status(data: RiderDispatchResponse):
    tasks = await query_get_dispatch_jungleworks_tasks(data.dispatch_request_id)  # type: ignore[misc,arg-type]
    return await _update_task_status(tasks.pickup_task_id, response_to_junglework_status[data.response])


async def update_task_status_from_delivery_state(data: RiderDeliveryState) -> list:
    tasks = await query_get_dispatch_jungleworks_tasks(data.dispatch_request_id)  # type: ignore[misc,arg-type]

    if data.state == DeliveryState.PICK_UP:
        return [
            await _update_task_status(tasks.pickup_task_id, JungleworksTaskStatus.SUCCESSFUL),
            await _update_task_status(tasks.delivery_task_id, JungleworksTaskStatus.STARTED),
        ]
    elif data.state == DeliveryState.COMPLETED:
        return [await _update_task_status(tasks.delivery_task_id, JungleworksTaskStatus.SUCCESSFUL)]
    else:
        return []


async def _retrieve_delivery_task_id(pickup_delivery_relationship):
    request_body = RetrieveDeliveryTaskIdRequestBody(pickup_delivery_relationship=pickup_delivery_relationship)
    return await call_jungleworks_api(path_namespace=RETRIEVE_DELIVERY_TASK_ID, body=request_body)


async def retrieve_delivery_task_id(pickup_delivery_relationship):
    return await _retrieve_delivery_task_id(pickup_delivery_relationship)


def should_connect_jungleworks(request):
    return settings.JUNGLEWORKS_ENABLE or (settings.DEBUG and request.META["QUERY_STRING"].startswith("JW"))
