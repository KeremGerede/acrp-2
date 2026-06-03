from typing import Optional
from app.core.config import settings
from app.utils.json_utils import extract_json


class LLMService:

    def __init__(self):
        self._model = None

    def _get_model(self):
        if self._model is None:
            import google.generativeai as genai
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self._model = genai.GenerativeModel(settings.GEMINI_MODEL)
        return self._model

    def generate(self, prompt: str) -> str:
        model = self._get_model()
        response = model.generate_content(prompt)
        return response.text

    def generate_json(self, prompt: str) -> Optional[dict]:
        text = self.generate(prompt)
        return extract_json(text)


llm_service = LLMService()
