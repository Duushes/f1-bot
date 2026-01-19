"""LLM service for content generation."""

from typing import List, Dict
from openai import OpenAI

from f1bot.config import settings
from f1bot.logging import get_logger

logger = get_logger(__name__)

client = OpenAI(api_key=settings.openai_api_key)


def generate_pre_race(race: Dict, news_context: List[Dict], lang: str) -> str:
    """Generate pre-race content (5-7 bullets)."""
    logger.info(f"Generating pre-race content for {race.get('name')} in {lang}")
    
    race_name = race.get("name", "Unknown Race")
    track = race.get("meta_json", {}).get("track", "Unknown Track") if isinstance(race.get("meta_json"), dict) else "Unknown Track"
    
    news_summary = "\n".join([f"- {n.get('title', '')}" for n in news_context[:5]])
    
    if lang == "ru":
        prompt = f"""Создай краткое превью гонки F1 для Gen Z аудитории. Будь нативным, используй эмодзи, но не переборщи.

Гонка: {race_name}
Трасса: {track}

Контекст из новостей:
{news_summary}

Требования:
- 5-7 буллетов
- Формат: каждый буллет с новой строки, начинается с эмодзи
- Включи: контекст трассы (1-2 факта), главную интригу, 2-3 пилота за кем следить, погоду/шины (кратко)
- Стиль: Gen Z, но информативно
- Не выдумывай факты, если не уверен - укажи "вероятно" или "по сообщениям"

Ответ (только текст, без дополнительных пояснений):"""
    else:
        prompt = f"""Create a brief F1 race preview for Gen Z audience. Be native, use emojis, but don't overdo it.

Race: {race_name}
Track: {track}

News context:
{news_summary}

Requirements:
- 5-7 bullets
- Format: each bullet on a new line, starts with emoji
- Include: track context (1-2 facts), main intrigue, 2-3 drivers to watch, weather/tires (briefly)
- Style: Gen Z, but informative
- Don't make up facts, if unsure - mention "probably" or "according to reports"

Response (text only, no additional explanations):"""
    
    try:
        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": "You are a Gen Z F1 content creator. Be concise, engaging, and authentic."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Error generating pre-race content: {e}")
        return "Ошибка генерации контента" if lang == "ru" else "Content generation error"


def generate_post_race(race: Dict, news_context: List[Dict], lang: str) -> str:
    """Generate post-race content (5-7 bullets)."""
    logger.info(f"Generating post-race content for {race.get('name')} in {lang}")
    
    race_name = race.get("name", "Unknown Race")
    news_summary = "\n".join([f"- {n.get('title', '')}" for n in news_context[:5]])
    
    if lang == "ru":
        prompt = f"""Создай краткий итог гонки F1 для Gen Z аудитории. Будь нативным, используй эмодзи.

Гонка: {race_name}

Контекст из новостей:
{news_summary}

Требования:
- 5-7 буллетов
- Формат: каждый буллет с новой строки, начинается с эмодзи
- Включи: победитель, ключевой момент гонки, что сломало стратегию, влияние на чемпионат, главный хайлайт
- Стиль: Gen Z, но информативно
- Не выдумывай факты, если не уверен - укажи "вероятно" или "по сообщениям"

Ответ (только текст, без дополнительных пояснений):"""
    else:
        prompt = f"""Create a brief F1 race recap for Gen Z audience. Be native, use emojis.

Race: {race_name}

News context:
{news_summary}

Requirements:
- 5-7 bullets
- Format: each bullet on a new line, starts with emoji
- Include: winner, key moment of the race, what broke the strategy, championship impact, main highlight
- Style: Gen Z, but informative
- Don't make up facts, if unsure - mention "probably" or "according to reports"

Response (text only, no additional explanations):"""
    
    try:
        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": "You are a Gen Z F1 content creator. Be concise, engaging, and authentic."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Error generating post-race content: {e}")
        return "Ошибка генерации контента" if lang == "ru" else "Content generation error"


def generate_bingo_meme_events(race: Dict, context: Dict, lang: str) -> List[Dict]:
    """Generate meme/contextual bingo events (4-6 items)."""
    logger.info(f"Generating bingo meme events for {race.get('name')} in {lang}")
    
    race_name = race.get("name", "Unknown Race")
    
    if lang == "ru":
        prompt = f"""Создай 4-6 мемных/контекстных событий для Bingo-карточки F1 гонки. События должны быть проверяемыми во время гонки, но с юмором/мемностью.

Гонка: {race_name}

Требования:
- 4-6 событий
- Каждое событие должно быть проверяемым (можно подтвердить во время гонки)
- Стиль: мемный, но реалистичный
- Формат JSON: [{{"id": "unique_id", "title": "Название события", "type": "meme"}}]

Примеры хороших событий:
- "Пилот обвиняет команду в радио"
- "Комментатор говорит 'Here we go'"
- "Пилот делает жест после обгона"

Ответ (только JSON массив, без дополнительного текста):"""
    else:
        prompt = f"""Create 4-6 meme/contextual events for F1 race Bingo card. Events should be verifiable during the race, but with humor/meme quality.

Race: {race_name}

Requirements:
- 4-6 events
- Each event should be verifiable (can be confirmed during the race)
- Style: meme, but realistic
- JSON format: [{{"id": "unique_id", "title": "Event title", "type": "meme"}}]

Examples of good events:
- "Driver blames team on radio"
- "Commentator says 'Here we go'"
- "Driver makes gesture after overtake"

Response (JSON array only, no additional text):"""
    
    try:
        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": "You are a Gen Z F1 content creator. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,
            max_tokens=300,
        )
        import json
        content = response.choices[0].message.content.strip()
        # Try to extract JSON from response
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        content = content.strip()
        return json.loads(content)
    except Exception as e:
        logger.error(f"Error generating bingo meme events: {e}")
        # Return default meme events
        if lang == "ru":
            return [
                {"id": "meme_1", "title": "Пилот обвиняет команду", "type": "meme"},
                {"id": "meme_2", "title": "Комментатор говорит 'Here we go'", "type": "meme"},
                {"id": "meme_3", "title": "Пилот делает жест", "type": "meme"},
                {"id": "meme_4", "title": "Мемный момент в радио", "type": "meme"},
            ]
        else:
            return [
                {"id": "meme_1", "title": "Driver blames team", "type": "meme"},
                {"id": "meme_2", "title": "Commentator says 'Here we go'", "type": "meme"},
                {"id": "meme_3", "title": "Driver makes gesture", "type": "meme"},
                {"id": "meme_4", "title": "Meme moment on radio", "type": "meme"},
            ]
