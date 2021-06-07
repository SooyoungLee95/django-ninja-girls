from unittest.mock import Mock, patch

import httpx
import pytest

from ras.common.integration.services.jungleworks.handlers import call_jungleworks_api
from ras.common.integration.services.jungleworks.schemas import JungleworksRequestBody

MOCK_PATH_NAMESPACE = "dummy"
MOCK_PATH = "/api/dummy"
MOCK_JUNGLEWORKS_PATHS = {MOCK_PATH_NAMESPACE: MOCK_PATH}


class MockRequestBody(JungleworksRequestBody):
    dummy_field: str


@pytest.mark.asyncio
@patch("ras.common.integration.services.jungleworks.handlers.JUNGLEWORKS_PATHS", MOCK_JUNGLEWORKS_PATHS)
@patch("ras.common.integration.services.jungleworks.handlers.AsyncExternalClient.request")
async def test_call_jungleworks_api_with_valid_namespace(mock_request):
    # Given: 요청/응답 함수를 mocking하고, 정의된 요청 및 응답값을 반환하도록 설정한 경우
    expected_response = {"message": "", "status": 200, "data": {}}
    mock_response = Mock()
    mock_response.json.side_effect = Mock(return_value=expected_response)
    mock_request.return_value = mock_response
    body = MockRequestBody(dummy_field="blahblah")

    # When: 정의된 Namespace값과 요청 바디로 Jungleworks API를 호출하면,
    response = await call_jungleworks_api(path_namespace=MOCK_PATH_NAMESPACE, body=body)

    # Then: 요청보내는 함수와 응답값 파싱하는 함수가 실행된다
    mock_request.assert_called_once()
    mock_request.return_value.json.assert_called_once()

    # And: 요청보내는 함수인자(path, body, method default) 값이 일치하고
    assert mock_request.call_args[0][0] == "POST"
    assert mock_request.call_args[0][1].endswith(MOCK_PATH)
    assert "api_key" in mock_request.call_args[1]["json"]
    assert "dummy_field" in mock_request.call_args[1]["json"]
    assert mock_request.call_args[1]["json"]["dummy_field"] == "blahblah"

    # And: 정의한 응답값이 올바르게 반환되는지 확인한다
    assert response == expected_response


@pytest.mark.asyncio
@patch("ras.common.integration.services.jungleworks.handlers.JUNGLEWORKS_PATHS", MOCK_JUNGLEWORKS_PATHS)
@patch("ras.common.integration.services.jungleworks.handlers.AsyncExternalClient.request")
async def test_call_jungleworks_api_with_invalid_namespace(mock_request):
    # Given: 요청/응답 함수를 mocking하고, 정의된 요청 및 응답값을 반환하도록 설정한 경우
    expected_response = {"message": "", "status": 200, "data": {}}
    mock_response = Mock()
    mock_response.json.side_effect = Mock(return_value=expected_response)
    mock_request.return_value = mock_response
    body = MockRequestBody(dummy_field="blahblah")

    # When: 정의된 Namespace값과 요청 바디로 Jungleworks API를 호출하면,
    invalid_path_namespace = "x"
    try:
        await call_jungleworks_api(path_namespace=invalid_path_namespace, body=body)
    except KeyError:
        # Then: KeyError가 반환되며 요청이 발생하지 않는다
        assert True
    else:
        raise AssertionError()
    mock_request.assert_not_called()
    mock_request.return_value.json.assert_not_called()


@pytest.mark.asyncio
@patch("ras.common.integration.services.jungleworks.handlers.JUNGLEWORKS_PATHS", MOCK_JUNGLEWORKS_PATHS)
@patch("ras.common.integration.services.jungleworks.handlers.AsyncExternalClient.request")
async def test_call_jungleworks_api_with_request_error(mock_request):
    # Given: 요청에서 RequestError가 발생하는 경우
    mock_request.side_effect = httpx.RequestError("test fail")
    body = MockRequestBody(dummy_field="blahblah")

    # When: 정의된 Namespace값과 요청 바디로 Jungleworks API를 호출하면,
    response = await call_jungleworks_api(path_namespace=MOCK_PATH_NAMESPACE, body=body)

    # Then: 요청보내는 함수만 실행되고,
    mock_request.assert_called_once()
    # And: 응답을 파싱하는 함수는 실행되지 않는다
    mock_request.return_value.json.assert_not_called()

    # And: 요청보내는 함수인자(path, body, method default) 값이 일치하고
    assert mock_request.call_args[0][0] == "POST"
    assert mock_request.call_args[0][1].endswith(MOCK_PATH)
    assert "api_key" in mock_request.call_args[1]["json"]
    assert "dummy_field" in mock_request.call_args[1]["json"]
    assert mock_request.call_args[1]["json"]["dummy_field"] == "blahblah"

    # And: 응답값은 None이 반환된다
    assert response is None
