import logging
import os

import firebase_admin
from firebase_admin import credentials, messaging
from firebase_admin.exceptions import (
    FirebaseError,
    InvalidArgumentError,
    OutOfRangeError,
)

from config.settings.base import BASE_DIR, FCM_SERVICE_ACCOUNT_KEY_FILENAME

cred_path = os.path.join(BASE_DIR, FCM_SERVICE_ACCOUNT_KEY_FILENAME)
cred = credentials.Certificate(cred_path)
firebase_admin.initialize_app(cred)
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
                response = messaging.send(message)
            except (InvalidArgumentError, OutOfRangeError, ValueError) as e:
                result["exception"] = f"{e!s}"
                break
            except (FirebaseError, IOError) as e:
                logger.error(f"[Firebase] retry: {try_count}, {e!r}")
                if try_count == retries - 1:
                    result["exception"] = f"{e!s}"
            else:
                if response:
                    result["success"] = True
                    break
        return result
