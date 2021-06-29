from http import HTTPStatus

from ninja.responses import Response


def validation_error_handler(request, exc):
    return Response(
        {"message": exc.errors[0]["msg"]},
        status=HTTPStatus.UNPROCESSABLE_ENTITY,
    )
