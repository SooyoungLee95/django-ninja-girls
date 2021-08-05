from typing import Union

import jwt
from cryptography.fernet import Fernet
from django.conf import settings

from ras.rider_app.schemas import AuthyoPayload

CIPHER = Fernet(key=settings.AUTHYO.FERNET_CRYPTO_KEY)


def get_encrypted_payload(payload: AuthyoPayload):
    return CIPHER.encrypt(payload.json().encode("utf-8")).decode("utf-8")


def decode_token(token) -> dict[str, Union[str, int]]:
    return jwt.decode(jwt=token, key=settings.AUTHYO.SECRET_KEY, algorithms=[settings.AUTHYO.ALGORITHM])
