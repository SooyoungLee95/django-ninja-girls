from cryptography.fernet import Fernet

from config.settings.base import AUTHYO_FERNET_CRYPTO_KEY
from ras.rider_app.schemas import AuthyoPayload

CIPHER = Fernet(key=AUTHYO_FERNET_CRYPTO_KEY)


class AuthyoTokenAuthenticator:
    def get_encrypted_payload(self, payload: AuthyoPayload):
        return CIPHER.encrypt(payload.json().encode("utf-8")).decode("utf-8")
