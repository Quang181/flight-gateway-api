import json
from functools import lru_cache
from pathlib import Path


LANGS_DIR = Path(__file__).with_name("langs")
DEFAULT_LANGUAGE = "en"


@lru_cache
def get_translations() -> dict[str, dict[str, str]]:
    translations: dict[str, dict[str, str]] = {}

    for file_path in sorted(LANGS_DIR.glob("*.json")):
        with file_path.open("r", encoding="utf-8") as file:
            translations[file_path.stem] = json.load(file)

    if not translations:
        raise RuntimeError("No translation files found in errors/langs")

    languages = list(translations)
    reference_keys = set(translations[languages[0]])
    for language in languages[1:]:
        current_keys = set(translations[language])
        if current_keys != reference_keys:
            raise RuntimeError(
                f"Translation keys mismatch for language '{language}'. "
                "All language files must have identical keys."
            )

    return translations


def resolve_language(accept_language: str | None) -> str:
    translations = get_translations()
    supported_languages = set(translations)

    if not accept_language:
        return DEFAULT_LANGUAGE

    for raw_language in accept_language.split(","):
        language = raw_language.split(";")[0].strip().lower()
        if language in supported_languages:
            return language

        base_language = language.split("-")[0]
        if base_language in supported_languages:
            return base_language

    return DEFAULT_LANGUAGE


def translate(message_key: str, accept_language: str | None = None) -> str:
    language = resolve_language(accept_language)
    translations = get_translations()
    language_messages = translations.get(language, translations[DEFAULT_LANGUAGE])
    default_messages = translations[DEFAULT_LANGUAGE]
    return language_messages.get(message_key, default_messages["unknown_error"])
