"""
OpenAI client wrapper with retry logic, timeout, and token tracking.
All AI calls go through this class to ensure consistent error handling.
"""
import time
from typing import Any
from openai import AsyncOpenAI, APIError, RateLimitError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.core.config import settings
from app.core.exceptions import AIServiceError
from app.core.logging import get_logger

logger = get_logger(__name__)


class OpenAIClient:
    def __init__(self) -> None:
        self._client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            timeout=settings.openai_timeout,
            max_retries=0,  # we handle retries via tenacity
        )

    @retry(
        retry=retry_if_exception_type((APIError, RateLimitError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def chat_completion(
        self,
        messages: list[dict],
        model: str | None = None,
        temperature: float = 0.3,
        response_format: dict | None = None,
    ) -> tuple[str, int, int]:
        """Returns (content, prompt_tokens, completion_tokens)."""
        model = model or settings.openai_text_model
        start = time.monotonic()
        try:
            kwargs: dict[str, Any] = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
            }
            if response_format:
                kwargs["response_format"] = response_format

            response = await self._client.chat.completions.create(**kwargs)
            content = response.choices[0].message.content or ""
            usage = response.usage
            latency_ms = int((time.monotonic() - start) * 1000)
            logger.info(
                "OpenAI chat completion",
                model=model,
                prompt_tokens=usage.prompt_tokens if usage else 0,
                completion_tokens=usage.completion_tokens if usage else 0,
                latency_ms=latency_ms,
            )
            return (
                content,
                usage.prompt_tokens if usage else 0,
                usage.completion_tokens if usage else 0,
            )
        except RateLimitError as e:
            logger.warning("OpenAI rate limit hit", error=str(e))
            raise
        except APIError as e:
            logger.error("OpenAI API error", error=str(e))
            raise
        except Exception as e:
            logger.error("Unexpected OpenAI error", error=str(e))
            raise AIServiceError(str(e)) from e

    @retry(
        retry=retry_if_exception_type((APIError, RateLimitError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def vision_completion(
        self,
        text_prompt: str,
        image_base64: str,
        system_prompt: str | None = None,
        model: str | None = None,
    ) -> tuple[str, int, int]:
        model = model or settings.openai_vision_model
        start = time.monotonic()
        try:
            messages: list[dict] = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({
                "role": "user",
                "content": [
                    {"type": "text", "text": text_prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64}",
                            "detail": "high",
                        },
                    },
                ],
            })
            response = await self._client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.2,
            )
            content = response.choices[0].message.content or ""
            usage = response.usage
            latency_ms = int((time.monotonic() - start) * 1000)
            logger.info(
                "OpenAI vision completion",
                model=model,
                prompt_tokens=usage.prompt_tokens if usage else 0,
                latency_ms=latency_ms,
            )
            return (
                content,
                usage.prompt_tokens if usage else 0,
                usage.completion_tokens if usage else 0,
            )
        except Exception as e:
            logger.error("OpenAI vision error", error=str(e))
            raise AIServiceError(f"Vision analysis failed: {e}") from e

    async def transcribe_audio(self, audio_bytes: bytes, filename: str = "audio.ogg") -> str:
        from io import BytesIO
        try:
            file_tuple = (filename, BytesIO(audio_bytes), "audio/ogg")
            response = await self._client.audio.transcriptions.create(
                model=settings.openai_whisper_model,
                file=file_tuple,  # type: ignore[arg-type]
                language="uk",
            )
            return response.text
        except Exception as e:
            logger.error("Whisper transcription error", error=str(e))
            raise AIServiceError(f"Transcription failed: {e}") from e


# Singleton client instance
openai_client = OpenAIClient()
