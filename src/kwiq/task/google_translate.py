import sys

import html
from os import environ

from pydantic import ConfigDict
from typing import Optional

from kwiq.core.task import Task
from kwiq.core.errors import ValidationError
from google.cloud import translate


class GoogleTranslate(Task):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    name: str = "google-translate"

    # Dictionary to store translations
    translation_cache: dict[str, str] = {}
    _google_project_id: Optional[str] = None
    _client: Optional[translate.TranslationServiceClient] = None

    @property
    def google_project_id(self) -> str:
        if self._google_project_id is None:
            proj_id = environ.get("GOOGLE_PROJECT_ID", "")
            if proj_id is None or proj_id == "":
                raise ValueError("env GOOGLE_PROJECT_ID must be set")
            self._google_project_id = f"projects/{proj_id}"
        return self._google_project_id

    @property
    def client(self) -> translate.TranslationServiceClient:
        if self._client is None:
            self._client = translate.TranslationServiceClient()
        return self._client

    def fn(self, text: str, target_language_code: str = "en") -> str:
        if self.client is None:
            raise ValidationError("Client can not be None")
        if self.google_project_id is None:
            raise ValidationError("google_project_id can not be None")

        if text in self.translation_cache:
            translated_text = self.translation_cache[text]
            print(f"Cache hit: {text}")
        else:
            print(f"Translating: {text}")
            try:
                translation = self.translate_text(text, target_language_code)
                translated_text = html.unescape(translation.translated_text)
                self.translation_cache[text] = translated_text

                print(f"→→→ Got translation: {translated_text}")
            except Exception as err:
                print(f"→→→ Got error in translation: {err}", file=sys.stderr)
                translated_text = "<ERROR>"

        return translated_text

    def translate_text(self, text: str, target_language_code: str) -> translate.Translation:
        max_retries = 3  # Maximum number of retries for API calls
        for attempt in range(max_retries):
            try:
                response = self.client.translate_text(
                    parent=self.google_project_id,
                    contents=[text],
                    target_language_code=target_language_code,
                )
                return response.translations[0]
            except Exception as e:
                if attempt < max_retries - 1:
                    continue
                else:
                    raise e
