from http import HTTPStatus

from ninja import Router

mock_post_router = Router()


@mock_post_router.get(
    "/mock_posts",
    url_name="mock_post_list",
    summary="전체 mock post의 list를 반환한다",
    response={200: None},
)
def retrieve_all_mock_posts(request):
    return HTTPStatus.OK
