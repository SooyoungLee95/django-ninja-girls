from ninja import NinjaAPI

from src.blog.views import mock_post_router

api = NinjaAPI(
    title="Django Girls Tutorial Final By Django Ninja For Rookie",
    description="Django Ninja와 함께하는 루키를 위한 장고걸스튜토리얼 파이널",
    version="0.0.1",
)

api.add_router("blog", mock_post_router)
