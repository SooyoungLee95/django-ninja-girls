from django.conf import settings
from ninja import Schema


class JungleworksResponseBody(Schema):
    message: str
    status: int
    data: dict


class JungleworksRequestBody(Schema):
    api_key: str = ""

    def dict(self, *args, **kwargs):
        _dict = super().dict(*args, **kwargs)
        _dict["api_key"] = settings.JUNGLEWORKS_API_KEY
        return _dict


class OnOffDutyRequestBody(JungleworksRequestBody):
    fleet_ids: list[int]
    is_available: int
