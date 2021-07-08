import logging

import jwt
from django.conf import settings
from jwt import InvalidTokenError
from ninja.security import HttpBearer

logger = logging.getLogger(__name__)


class RideryoAuth(HttpBearer):
    def authenticate(self, request, token):
        try:
            jwt.decode(jwt=token, key=settings.AUTHYO.SECRET_KEY, algorithms=[settings.AUTHYO.ALGORITHM])
        except (AttributeError, InvalidTokenError) as e:
            logger.error(f"[RideryoAuth] {e!r}")
            return None
        return token
