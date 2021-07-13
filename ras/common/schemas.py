from ninja import Schema


class ErrorResponse(Schema):
    message: str = ""
