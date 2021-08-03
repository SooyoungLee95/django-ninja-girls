import logging
from http import HTTPStatus

from hubyo_client.client import HubyoClientError
from ninja.errors import HttpError

from ras.common.sms.connections import hubyo_client
from ras.rider_app.schemas import SMSMessageData, SMSMessageInfo

logger = logging.getLogger(__name__)


def send_sms_via_hubyo(phone_number, verification_code):
    sms_message_info = SMSMessageInfo(
        tracking_id=phone_number,
        msg={"data": SMSMessageData(target=phone_number, text=f"[요기요라이더] 인증번호는 {verification_code} 입니다.")},
    ).dict()

    try:
        response = hubyo_client.send(**sms_message_info)
    except HubyoClientError as e:
        logger.error(f"[SMS] hubyo client error {e!r}")
    except Exception as e:
        logger.critical(f"[SMS] unexpected error {e!r}")
    else:
        logger.info(f"[SMS] hubyo client sent SMS - {response}")
        return
    raise HttpError(HTTPStatus.INTERNAL_SERVER_ERROR, "인증번호 SMS 전송에 실패 하였습니다.")
