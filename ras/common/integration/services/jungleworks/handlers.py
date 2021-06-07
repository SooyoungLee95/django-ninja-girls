import logging
from typing import Optional
from urllib.parse import urljoin

import httpx
from django.conf import settings

from ras.rider_app.schemas import RiderAvailability

from ...connection import AsyncExternalClient
from .schemas import (
    JungleworksRequestBody,
    JungleworksResponseBody,
    OnOffDutyRequestBody,
)

ON_OFF_DUTY = "on_off_duty"
JUNGLEWORKS_PATHS = {
    ON_OFF_DUTY: "/v2/change_fleet_availability",
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


def should_connect_jungleworks(request):
    return settings.JUNGLEWORKS_ENABLE or (settings.DEBUG and request.META["QUERY_STRING"] == "JW")
