import logging
import os
from typing import Union

import firebase_admin
from firebase_admin import credentials, messaging
from firebase_admin.exceptions import (
    FirebaseError,
    InvalidArgumentError,
    OutOfRangeError,
)

from config.settings.base import BASE_DIR, FCM_SERVICE_ACCOUNT_KEY_FILENAME

logger = logging.getLogger(__name__)


class FCMSender:
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, "_instance"):
            cred_path = os.path.join(BASE_DIR, FCM_SERVICE_ACCOUNT_KEY_FILENAME)
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, *args, **kwargs):
        cls = type(self)
        if not hasattr(cls, "_init"):
            cls._init = True  # type: ignore[attr-defined]

    def _create_fcm(self, data):
        title = data.pop("title")
        body = data.pop("body")
        token = data.pop("registration_token")
        return messaging.Message(
            token=token,
            apns=messaging.APNSConfig(
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(alert=messaging.ApsAlert(title=title, body=body)),
                    data=data,
                )
            ),
            android=messaging.AndroidConfig(
                notification=messaging.AndroidNotification(title=title, body=body),
                data=data,
            ),
        )

    def send(self, data, retries=3):
        result: dict[str, Union[bool, str]] = {
            "success": False,
        }
        message = self._create_fcm(data)
        for try_count in range(retries):
            try:
                messaging.send(message)
            except (InvalidArgumentError, OutOfRangeError, ValueError) as e:
                result["exception"] = f"{e!s}"
                break
            except (FirebaseError, Exception) as e:
                logger.error(f"[Firebase] retry: {try_count}, {e!r}")
                if try_count == retries - 1:
                    result["exception"] = f"{e!s}"
            else:
                result["success"] = True
                break
        return result
