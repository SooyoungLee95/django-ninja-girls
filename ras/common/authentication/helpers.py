from cryptography.fernet import Fernet

from config.settings.local import AUTHYO
from ras.rider_app.schemas import AuthyoPayload

CIPHER = Fernet(key=AUTHYO.AUTHORIZATION_CODE_FERNET_KEY)


class AuthyoTokenAuthenticator:
    @classmethod
    def get_encrypted_payload(cls, payload: AuthyoPayload):
        return CIPHER.encrypt(payload.json().encode("utf-8")).decode("utf-8")
