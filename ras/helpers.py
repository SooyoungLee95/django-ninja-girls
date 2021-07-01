import logging
from http import HTTPStatus

from ninja.responses import Response

logger = logging.getLogger(__name__)


def validation_error_handler(request, exc):
    errors = [f"{err['type']}:{err['msg']}" for err in exc.errors]
    logger.error(f"[ApiValidationError {request.method} {request.path}] {','.join(errors)}")
    return Response(data={"message": "요청을 처리할 수 없습니다."}, status=HTTPStatus.UNPROCESSABLE_ENTITY)
