import logging

from firebase_admin import messaging
from firebase_admin.exceptions import FirebaseError, InvalidArgumentError, OutOfRangeError

logger = logging.getLogger(__name__)


class FCMSender:
    def send(self, data, retries=3):
        result = {
            "success": False,
        }
        message = messaging.Message(
            token=data.pop("registration_token"),
            data=data,
            notification=messaging.Notification(
                title=data.pop("title"),
                body=data.pop("body"),
            ),
        )
        for try_count in range(retries):
            try:
                messaging.send(message)
            except (InvalidArgumentError, OutOfRangeError, ValueError) as e:
                result["exception"] = f"{e!s}"
                return result
            except (FirebaseError, IOError) as e:
                logger.error(f"[Firebase] retry: {try_count}, {e!r}")
            else:
                result["success"] = True
                return result

