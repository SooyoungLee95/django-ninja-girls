import logging
from typing import Any

from hubyo_client.client import HubyoClientError

from ras.common.sms.connections import hubyo_client

logger = logging.getLogger(__name__)


def send_sms_via_hubyo(info: dict[str, Any]) -> dict[str, Any]:
    try:
        response = hubyo_client.send(**info)
    except HubyoClientError as e:
        logger.error(f"[SMS] hubyo client error {e!r}")
    except Exception as e:
        logger.critical(f"[SMS] unexpected error {e!r}")
    else:
        logger.info(f"[SMS] hubyo client sent SMS - {response}")
        return response
    return {}
