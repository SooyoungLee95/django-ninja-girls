from http import HTTPStatus

from ninja.responses import Response


def validation_error_handler(request, exc):
    return Response(
        {"errors": {"message": "요청 유효성 에러가 발생 하였습니다."}},
        status=HTTPStatus.UNPROCESSABLE_ENTITY,
    )
