from typing import Union

import jwt
from cryptography.fernet import Fernet
from django.conf import settings

from ras.rider_app.schemas import AuthyoPayload

CIPHER = Fernet(key=settings.AUTHYO.FERNET_CRYPTO_KEY)


def get_encrypted_payload(payload: AuthyoPayload):
    return CIPHER.encrypt(payload.json().encode("utf-8")).decode("utf-8")


def extract_jwt_payload(request) -> dict[str, Union[str, int]]:
    _, token = request.headers["Authorization"].split()
    return jwt.decode(jwt=token, key=settings.AUTHYO.SECRET_KEY, algorithms=[settings.AUTHYO.ALGORITHM])
