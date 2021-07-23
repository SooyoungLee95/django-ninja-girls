import logging

import jwt
from django.conf import settings
from jwt import InvalidTokenError
from ninja.security import HttpBearer

from ras.rider_app.enums import RideryoRole
from ras.rideryo.models import RiderProfile

logger = logging.getLogger(__name__)

AUTHORIZED_ROLES = {r.value for r in RideryoRole}


class RideryoAuth(HttpBearer):
    def authenticate(self, request, token):
        try:
            payload = jwt.decode(jwt=token, key=settings.AUTHYO.SECRET_KEY, algorithms=[settings.AUTHYO.ALGORITHM])
        except InvalidTokenError as e:
            logger.error(f"[RideryoAuth] {e!r}")
            return None

        if not self._validate_payload(payload):
            return None

        try:
            rider = RiderProfile.objects.get(rider_id=payload["sub_id"])
        except RiderProfile.DoesNotExist as e:
            logger.error(f"[RideryoAuth] {e!r}")
            return None

        return rider

    def _validate_payload(self, payload):
        try:
            return bool(
                payload["sub_id"]
                and payload["platform"] == settings.RIDERYO_BASE_URL
                and payload["base_url"] == settings.RIDERYO_ENV
                and payload["role"] in AUTHORIZED_ROLES
            )
        except KeyError as e:
            logger.error(f"[RideryoAuth] {e!r}")
            return False
