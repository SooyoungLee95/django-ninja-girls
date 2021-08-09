import re

from django.core.exceptions import ValidationError

from ras.rider_app.constants import (
    MSG_INVALID_PASSWORD_CREATION_CONDITION,
    REGEX_PASSWORD_CONDITION,
)


class RiderAppPasswordConditionValidator:
    def validate(self, password, user=None):
        if not re.match(REGEX_PASSWORD_CONDITION, password):
            raise ValidationError(message=MSG_INVALID_PASSWORD_CREATION_CONDITION)

    def get_help_text(self):
        return "최소 8자 / 최소 1개의 영 소문자, 대문자 / 최소 1개의 특수문자 / 최소 1개의 숫자"
