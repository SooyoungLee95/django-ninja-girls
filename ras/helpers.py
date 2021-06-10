from http import HTTPStatus

from ninja.responses import Response


def validation_error_handler(request, exc):
    return Response(
        {"errors": [{"name": ".".join(err["loc"]), "message": f"{err['type']}: {err['msg']}"} for err in exc.errors]},
        status=HTTPStatus.UNPROCESSABLE_ENTITY,
    )
