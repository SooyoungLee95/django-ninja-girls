import re

from django.core.exceptions import ValidationError

from ras.rider_app.constants import (
    MSG_INVALID_PASSWORD_CREATION_CONDITION,
    REGEX_PASSWORD_CONDITION,
)

password_condition = re.compile(REGEX_PASSWORD_CONDITION, re.X)


class RiderAppPasswordConditionValidator:
    def validate(self, password, user=None):
        if not password_condition.match(password):
            raise ValidationError(message=MSG_INVALID_PASSWORD_CREATION_CONDITION)

    def get_help_text(self):
        return "최소 8자 / 최소 1개의 영 소문자, 대문자 / 최소 1개의 특수문자 / 최소 1개의 숫자"
