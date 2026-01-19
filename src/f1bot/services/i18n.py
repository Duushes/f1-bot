"""Internationalization service."""

from typing import Dict

# Translation keys
TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "ru": {
        "menu.welcome": "🏎️ Добро пожаловать в F1 Bot!\n\nВыберите действие:",
        "menu.pre_race": "📋 F1 in 60 Seconds",
        "menu.bingo": "🎯 Bingo Cards",
        "menu.post_race": "🏁 Race Result in 60 Seconds",
        "menu.language": "🌐 Язык",
        "menu.pre_race_coming_soon": "Скоро здесь будет превью гонки!",
        "menu.bingo_coming_soon": "Скоро здесь будут Bingo Cards!",
        "menu.post_race_coming_soon": "Скоро здесь будут итоги гонки!",
        "menu.back": "🔙 Назад",
        "bingo.title": "🎯 Bingo Cards\n\nГонка: {race_name}\n\nОтмечайте события во время гонки:",
        "bingo.finish": "✅ Завершить ({count}/{total})",
        "bingo.finish_result": "🎉 Bingo завершён!\n\nЗакрашено: {checked} из {total} клеток\nГонка: {race_name}",
        "bingo.no_race": "❌ Нет предстоящих гонок",
    },
    "en": {
        "menu.welcome": "🏎️ Welcome to F1 Bot!\n\nChoose an action:",
        "menu.pre_race": "📋 F1 in 60 Seconds",
        "menu.bingo": "🎯 Bingo Cards",
        "menu.post_race": "🏁 Race Result in 60 Seconds",
        "menu.language": "🌐 Language",
        "menu.pre_race_coming_soon": "Pre-race preview coming soon!",
        "menu.bingo_coming_soon": "Bingo Cards coming soon!",
        "menu.post_race_coming_soon": "Race results coming soon!",
        "menu.back": "🔙 Back",
        "bingo.title": "🎯 Bingo Cards\n\nRace: {race_name}\n\nMark events during the race:",
        "bingo.finish": "✅ Finish ({count}/{total})",
        "bingo.finish_result": "🎉 Bingo completed!\n\nMarked: {checked} out of {total} cells\nRace: {race_name}",
        "bingo.no_race": "❌ No upcoming races",
    },
}


def t(key: str, lang: str = "ru", **kwargs) -> str:
    """Translate a key to the specified language."""
    translations = TRANSLATIONS.get(lang, TRANSLATIONS["ru"])
    text = translations.get(key, key)
    
    # Simple placeholder replacement
    if kwargs:
        for k, v in kwargs.items():
            text = text.replace(f"{{{k}}}", str(v))
    
    return text
