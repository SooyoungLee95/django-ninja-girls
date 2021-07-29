import logging
from typing import Any

from hubyo_client.client import HubyoClientError

from ras.common.sms.connections import hubyo_client

logger = logging.getLogger(__name__)


def send_sms_via_hubyo(info: dict[str, Any]) -> dict[str, Any]:
    try:
        response = hubyo_client.send(**info)
        return response
    except HubyoClientError as e:
        logger.critical(f"[SMS] hubyoclient error {e!r}")
    return {}
