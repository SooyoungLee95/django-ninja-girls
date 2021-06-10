from ninja import Schema


class ErrorItem(Schema):
    name: str
    message: str


class ErrorResponse(Schema):
    errors: list[ErrorItem] = []
