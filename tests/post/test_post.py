from django.test import Client
from django.urls import reverse

client = Client()


class TestMockPostList:
    def test_mock_post_list_should_return_200(self):
        assert client.get(reverse("ninja:mock_post_list")).status_code == 200
