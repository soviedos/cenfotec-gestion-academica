"""Unit tests for GeminiGateway retry logic with exponential backoff."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from google.genai import errors as genai_errors
from google.genai import types

from app.modules.evaluacion_docente.domain.exceptions import GeminiUnavailableError
from app.modules.evaluacion_docente.infrastructure.external.gemini_gateway import (
    _MAX_RETRIES,
    _RETRY_BASE_DELAY,
    _RETRY_MAX_DELAY,
    GeminiGateway,
)

_GW_MOD = "app.modules.evaluacion_docente.infrastructure.external.gemini_gateway"


def _server_error(msg: str = "500") -> genai_errors.ServerError:
    return genai_errors.ServerError(500, {"error": {"message": msg}})


def _client_error(msg: str = "400") -> genai_errors.ClientError:
    return genai_errors.ClientError(400, {"error": {"message": msg}})


@pytest.fixture
def mock_client():
    """Patch genai.Client to avoid needing a real API key."""
    with patch(f"{_GW_MOD}.genai.Client") as mock:
        client_instance = MagicMock()
        mock.return_value = client_instance
        yield client_instance


@pytest.fixture
def gateway(mock_client):
    return GeminiGateway(api_key="test-key", max_retries=2)


class TestCallWithRetry:
    @pytest.mark.asyncio
    async def test_succeeds_on_first_attempt(self, gateway, mock_client):
        mock_response = MagicMock()
        mock_response.text = "test response"
        mock_response.usage_metadata = MagicMock(
            prompt_token_count=10,
            candidates_token_count=20,
        )

        mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)

        result = await gateway._call_with_retry(
            mock_client.aio.models,
            model="test-model",
            contents="hello",
            config=types.GenerateContentConfig(temperature=0.3),
        )

        assert result == mock_response
        assert mock_client.aio.models.generate_content.call_count == 1

    @pytest.mark.asyncio
    async def test_retries_on_server_error(self, gateway, mock_client):
        mock_response = MagicMock()
        mock_response.text = "ok"

        mock_client.aio.models.generate_content = AsyncMock(
            side_effect=[
                _server_error("500 Internal"),
                mock_response,
            ]
        )

        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await gateway._call_with_retry(
                mock_client.aio.models,
                model="test-model",
                contents="hello",
                config=types.GenerateContentConfig(temperature=0.3),
            )

        assert result == mock_response
        assert mock_client.aio.models.generate_content.call_count == 2

    @pytest.mark.asyncio
    async def test_retries_on_timeout_error(self, gateway, mock_client):
        mock_response = MagicMock()
        mock_response.text = "ok"

        mock_client.aio.models.generate_content = AsyncMock(
            side_effect=[
                TimeoutError("request timed out"),
                mock_response,
            ]
        )

        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await gateway._call_with_retry(
                mock_client.aio.models,
                model="test-model",
                contents="hello",
                config=types.GenerateContentConfig(temperature=0.3),
            )

        assert result == mock_response
        assert mock_client.aio.models.generate_content.call_count == 2

    @pytest.mark.asyncio
    async def test_raises_after_max_retries(self, gateway, mock_client):
        mock_client.aio.models.generate_content = AsyncMock(side_effect=_server_error("500 always"))

        with patch("asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(genai_errors.ServerError):
                await gateway._call_with_retry(
                    mock_client.aio.models,
                    model="test-model",
                    contents="hello",
                    config=types.GenerateContentConfig(temperature=0.3),
                )

        # max_retries=2 → 3 total attempts (initial + 2 retries)
        assert mock_client.aio.models.generate_content.call_count == 3

    @pytest.mark.asyncio
    async def test_does_not_retry_client_error(self, gateway, mock_client):
        mock_client.aio.models.generate_content = AsyncMock(
            side_effect=_client_error("400 Bad Request")
        )

        with pytest.raises(genai_errors.ClientError):
            await gateway._call_with_retry(
                mock_client.aio.models,
                model="test-model",
                contents="hello",
                config=types.GenerateContentConfig(temperature=0.3),
            )

        assert mock_client.aio.models.generate_content.call_count == 1

    @pytest.mark.asyncio
    async def test_exponential_backoff_delays(self, gateway, mock_client):
        mock_response = MagicMock()
        mock_response.text = "ok"

        mock_client.aio.models.generate_content = AsyncMock(
            side_effect=[
                _server_error("fail 1"),
                _server_error("fail 2"),
                mock_response,
            ]
        )

        sleep_calls = []

        async def mock_sleep(delay):
            sleep_calls.append(delay)

        with patch("asyncio.sleep", side_effect=mock_sleep):
            await gateway._call_with_retry(
                mock_client.aio.models,
                model="test-model",
                contents="hello",
                config=types.GenerateContentConfig(temperature=0.3),
            )

        # attempt 0 → delay = min(1.0 * 2^0, 16.0) = 1.0
        # attempt 1 → delay = min(1.0 * 2^1, 16.0) = 2.0
        assert sleep_calls == [_RETRY_BASE_DELAY * 1, _RETRY_BASE_DELAY * 2]


class TestRetryConstants:
    def test_max_retries_is_positive(self):
        assert _MAX_RETRIES >= 1

    def test_base_delay_is_positive(self):
        assert _RETRY_BASE_DELAY > 0

    def test_max_delay_exceeds_base(self):
        assert _RETRY_MAX_DELAY >= _RETRY_BASE_DELAY


class TestGeminiGatewayInit:
    def test_raises_without_api_key(self):
        with pytest.raises(GeminiUnavailableError):
            GeminiGateway(api_key="")

    def test_accepts_custom_max_retries(self, mock_client):
        gw = GeminiGateway(api_key="key", max_retries=5)
        assert gw._max_retries == 5
