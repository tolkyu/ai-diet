from app.ai.client import openai_client
from app.ai.nutrition_analyzer import FoodAnalysisResult, NutritionAnalyzer
from app.core.logging import get_logger

logger = get_logger(__name__)


class VoiceProcessor:
    def __init__(self) -> None:
        self._analyzer = NutritionAnalyzer()

    async def process_voice_to_food(
        self, audio_bytes: bytes, filename: str = "voice.ogg"
    ) -> tuple[str, FoodAnalysisResult]:
        """Transcribe voice message and analyze as food input."""
        transcribed_text = await openai_client.transcribe_audio(audio_bytes, filename)
        logger.info("Voice transcribed", length=len(transcribed_text))

        result = await self._analyzer.analyze_text(transcribed_text)
        return transcribed_text, result


voice_processor = VoiceProcessor()
