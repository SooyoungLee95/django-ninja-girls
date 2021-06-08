from http import HTTPStatus

from django.conf import settings
from ninja import Schema

# https://tookanapi.docs.apiary.io/#introduction/error-codes
_relevant_status = {
    101: HTTPStatus.BAD_REQUEST,  # INVALID_KEY
    100: HTTPStatus.BAD_REQUEST,  # PARAMETER_MISSING
    200: HTTPStatus.OK,  # ACTION_COMPLETE
    201: HTTPStatus.BAD_REQUEST,  # SHOW_ERROR_MESSAGE
    404: HTTPStatus.BAD_REQUEST,  # ERROR_IN_EXECUTION
}


class JungleworksResponseBody(Schema):
    message: str
    status: int
    data: dict

    def relevant_http_status(self) -> HTTPStatus:
        return _relevant_status[self.status]


class JungleworksRequestBody(Schema):
    api_key: str = ""

    def dict(self, *args, **kwargs):
        _dict = super().dict(*args, **kwargs)
        _dict["api_key"] = settings.JUNGLEWORKS_API_KEY
        return _dict


class OnOffDutyRequestBody(JungleworksRequestBody):
    fleet_ids: list[int]
    is_available: int
