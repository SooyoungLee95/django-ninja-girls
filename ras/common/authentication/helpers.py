from http import HTTPStatus
from typing import Union

import jwt
from cryptography.fernet import Fernet
from django.conf import settings
from django.core import signing
from ninja.errors import HttpError

from ras.rider_app.constants import (
    MSG_INVALID_TOKEN,
    MSG_TOKEN_EXPIRED,
    VERIFY_TOKEN_MAX_AGE,
)
from ras.rider_app.schemas import AuthyoPayload, VerificationInfo

CIPHER = Fernet(key=settings.AUTHYO.FERNET_CRYPTO_KEY)


def get_encrypted_payload(payload: AuthyoPayload):
    return CIPHER.encrypt(payload.json().encode("utf-8")).decode("utf-8")


def decode_token(token) -> dict[str, Union[str, int]]:
    return jwt.decode(jwt=token, key=settings.AUTHYO.SECRET_KEY, algorithms=[settings.AUTHYO.ALGORITHM])


def generate_jwt_for_password_reset(rider_id, data: VerificationInfo):
    return signing.dumps(
        {"rider_id": rider_id, "phone_number": data.phone_number, "verification_code": data.verification_code},
        compress=True,
    )


def generate_jwt_for_verification_code_check(rider_id):
    return signing.dumps({"rider_id": rider_id}, compress=True)


def decode_token_for_password_reset(token: str, max_age: int = VERIFY_TOKEN_MAX_AGE) -> dict:
    try:
        payload = signing.loads(token, max_age=max_age)
    except signing.SignatureExpired:
        raise HttpError(HTTPStatus.BAD_REQUEST, MSG_TOKEN_EXPIRED)
    except signing.BadSignature:
        raise HttpError(HTTPStatus.BAD_REQUEST, MSG_INVALID_TOKEN)
    else:
        return payload
