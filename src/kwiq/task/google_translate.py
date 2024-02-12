from pathlib import Path

import sys

import html
from os import environ

from pydantic import ConfigDict
from typing import Optional

from kwiq.core.task import Task
from kwiq.core.errors import ValidationError
from google.cloud import translate
from kwiq.db.sqlite import DB as SqliteDb


class GoogleTranslate(Task):
    name: str = "google-translate"

    # Dictionary to store translations
    translation_cache_path: Optional[Path] = None
    __translation_cache: Optional[dict[str, str]] = None
    __translation_cache_db: Optional[SqliteDb] = None
    __google_project_id: Optional[str] = None
    __client: Optional[translate.TranslationServiceClient] = None

    @property
    def translation_cache(self):
        if self.__translation_cache is None:
            if self.translation_cache_path is not None:
                self.__translation_cache_db = SqliteDb(db_path=self.translation_cache_path)
                self.__translation_cache = dict(self.__translation_cache_db.select(
                    sql="SELECT original_text, translated_text FROM translations"))
                print("Read translation cache of size: ", len(self.__translation_cache))
            else:
                self.__translation_cache = {}

        return self.__translation_cache

    @property
    def google_project_id(self) -> str:
        if self.__google_project_id is None:
            proj_id = environ.get("GOOGLE_PROJECT_ID", "")
            if proj_id is None or proj_id == "":
                raise ValueError("env GOOGLE_PROJECT_ID must be set")
            self.__google_project_id = f"projects/{proj_id}"
        return self.__google_project_id

    @property
    def client(self) -> translate.TranslationServiceClient:
        if self.__client is None:
            self.__client = translate.TranslationServiceClient()
        return self.__client

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

                if self.__translation_cache_db is not None:
                    self.__translation_cache_db.command(sql='''
                        INSERT INTO translations (original_text, translated_text)
                            VALUES (?, ?)
                            ON CONFLICT(original_text) DO UPDATE SET
                            translated_text = excluded.translated_text
                        ''',
                                                        parameters=(text, translated_text)
                                                        )

                print(f"→→→ Got translation: {translated_text}")
            except Exception as err:
                print(f"→→→ Got error in translation: {err}", file=sys.stderr)
                translated_text = "<ERROR>"

        return translated_text

    def close(self):
        pass

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
