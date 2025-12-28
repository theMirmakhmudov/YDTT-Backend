"""
Internationalization (i18n) support.
"""
from typing import Dict, Optional
import json
from pathlib import Path

from app.core.config import settings


# Load translations from JSON files
_translations: Dict[str, Dict[str, str]] = {}


def load_translations():
    """Load all translation files."""
    global _translations
    translations_dir = Path(__file__).parent / "translations"
    
    for lang in settings.SUPPORTED_LANGUAGES:
        lang_file = translations_dir / f"{lang}.json"
        if lang_file.exists():
            with open(lang_file, "r", encoding="utf-8") as f:
                _translations[lang] = json.load(f)
        else:
            _translations[lang] = {}


def get_translation(key: str, language: str = None, **kwargs) -> str:
    """
    Get a translated string by key.
    
    Args:
        key: The translation key (e.g., "auth.login.success")
        language: The language code (defaults to settings.DEFAULT_LANGUAGE)
        **kwargs: Format arguments for the translation string
    
    Returns:
        The translated string, or the key if not found
    """
    if not _translations:
        load_translations()
    
    lang = language or settings.DEFAULT_LANGUAGE
    
    # Try to get translation in requested language
    translations = _translations.get(lang, {})
    value = translations.get(key)
    
    # Fallback to default language
    if value is None and lang != settings.DEFAULT_LANGUAGE:
        translations = _translations.get(settings.DEFAULT_LANGUAGE, {})
        value = translations.get(key)
    
    # Return key if no translation found
    if value is None:
        return key
    
    # Apply format arguments
    if kwargs:
        try:
            value = value.format(**kwargs)
        except KeyError:
            pass
    
    return value


def t(key: str, language: str = None, **kwargs) -> str:
    """Shorthand for get_translation."""
    return get_translation(key, language, **kwargs)


# Common error messages
class Messages:
    """Common translatable messages."""
    
    @staticmethod
    def auth_invalid_credentials(lang: str = None) -> str:
        return t("auth.invalid_credentials", lang)
    
    @staticmethod
    def auth_token_expired(lang: str = None) -> str:
        return t("auth.token_expired", lang)
    
    @staticmethod
    def auth_unauthorized(lang: str = None) -> str:
        return t("auth.unauthorized", lang)
    
    @staticmethod
    def user_not_found(lang: str = None) -> str:
        return t("user.not_found", lang)
    
    @staticmethod
    def exam_not_found(lang: str = None) -> str:
        return t("exam.not_found", lang)
    
    @staticmethod
    def exam_expired(lang: str = None) -> str:
        return t("exam.expired", lang)
    
    @staticmethod
    def validation_required(field: str, lang: str = None) -> str:
        return t("validation.required", lang, field=field)
