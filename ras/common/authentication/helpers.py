import logging
from http import HTTPStatus
from typing import Union

import jwt
from cryptography.fernet import Fernet
from django.conf import settings
from django.core.handlers.wsgi import WSGIRequest
from ninja.errors import HttpError

from ras.rider_app.constants import MSG_UNAUTHORIZED
from ras.rider_app.schemas import AuthyoPayload

CIPHER = Fernet(key=settings.AUTHYO.FERNET_CRYPTO_KEY)


logger = logging.getLogger(__name__)


def get_encrypted_payload(payload: AuthyoPayload):
    return CIPHER.encrypt(payload.json().encode("utf-8")).decode("utf-8")


def extract_jwt_payload(token) -> dict[str, Union[str, int]]:
    try:
        return jwt.decode(jwt=token, key=settings.AUTHYO.SECRET_KEY, algorithms=[settings.AUTHYO.ALGORITHM])
    except jwt.DecodeError as e:
        logger.error(f"[extract_jwt_payload] {e!r}")
        raise HttpError(HTTPStatus.UNAUTHORIZED, MSG_UNAUTHORIZED)


def parse_token(request: WSGIRequest):
    authorization = request.headers.get("Authorization")
    if not authorization:
        raise HttpError(HTTPStatus.UNAUTHORIZED, MSG_UNAUTHORIZED)
    _, token = authorization.split()
    return token
