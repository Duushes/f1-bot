"""Data repositories."""

import json
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import text

from f1bot.storage.db import get_db
from f1bot.logging import get_logger

logger = get_logger(__name__)


class UserRepo:
    """User repository."""

    def get(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """Get user by Telegram ID."""
        db = get_db()
        try:
            result = db.execute(
                text("SELECT * FROM users WHERE telegram_id = :id"),
                {"id": telegram_id}
            ).fetchone()
            
            if result:
                return {
                    "telegram_id": result[0],
                    "lang": result[1],
                    "created_at": result[2],
                    "updated_at": result[3],
                }
            return None
        finally:
            db.close()

    def create_or_update(self, telegram_id: int, lang: Optional[str] = None) -> None:
        """Create or update user."""
        db = get_db()
        try:
            existing = self.get(telegram_id)
            if existing:
                if lang:
                    db.execute(
                        text("UPDATE users SET lang = :lang, updated_at = CURRENT_TIMESTAMP WHERE telegram_id = :id"),
                        {"id": telegram_id, "lang": lang}
                    )
            else:
                db.execute(
                    text("INSERT INTO users (telegram_id, lang) VALUES (:id, :lang)"),
                    {"id": telegram_id, "lang": lang or "ru"}
                )
            db.commit()
        finally:
            db.close()


class RaceRepo:
    """Race repository."""

    def upsert(self, race_id: str, name: str, start_time_utc: datetime, status: str, meta_json: Optional[Dict] = None) -> None:
        """Upsert race."""
        db = get_db()
        try:
            meta_str = json.dumps(meta_json) if meta_json else None
            db.execute(
                text("""
                    INSERT OR REPLACE INTO races (race_id, name, start_time_utc, status, meta_json)
                    VALUES (:id, :name, :start_time, :status, :meta)
                """),
                {
                    "id": race_id,
                    "name": name,
                    "start_time": start_time_utc,
                    "status": status,
                    "meta": meta_str,
                }
            )
            db.commit()
        finally:
            db.close()

    def get_next_race(self) -> Optional[Dict[str, Any]]:
        """Get next upcoming race."""
        db = get_db()
        try:
            result = db.execute(
                text("SELECT * FROM races WHERE status = 'upcoming' ORDER BY start_time_utc LIMIT 1")
            ).fetchone()
            
            if result:
                return {
                    "race_id": result[0],
                    "name": result[1],
                    "start_time_utc": result[2],
                    "status": result[3],
                    "meta_json": json.loads(result[4]) if result[4] else None,
                }
            return None
        finally:
            db.close()

    def get_last_race(self) -> Optional[Dict[str, Any]]:
        """Get last finished race."""
        db = get_db()
        try:
            result = db.execute(
                text("SELECT * FROM races WHERE status = 'finished' ORDER BY start_time_utc DESC LIMIT 1")
            ).fetchone()
            
            if result:
                return {
                    "race_id": result[0],
                    "name": result[1],
                    "start_time_utc": result[2],
                    "status": result[3],
                    "meta_json": json.loads(result[4]) if result[4] else None,
                }
            return None
        finally:
            db.close()


class ContentRepo:
    """Content repository."""

    def save_draft(self, race_id: str, content_type: str, lang: str, text: str) -> None:
        """Save draft content."""
        self._upsert(race_id, content_type, lang, "draft", text)

    def mark_pending(self, race_id: str, content_type: str, lang: str) -> None:
        """Mark content as pending admin approval."""
        db = get_db()
        try:
            db.execute(
                text("UPDATE contents SET status = 'pending_admin', updated_at = CURRENT_TIMESTAMP WHERE race_id = :race_id AND content_type = :type AND lang = :lang"),
                {"race_id": race_id, "type": content_type, "lang": lang}
            )
            db.commit()
        finally:
            db.close()

    def approve(self, race_id: str, content_type: str, lang: str) -> None:
        """Approve content."""
        db = get_db()
        try:
            db.execute(
                text("UPDATE contents SET status = 'approved', updated_at = CURRENT_TIMESTAMP WHERE race_id = :race_id AND content_type = :type AND lang = :lang"),
                {"race_id": race_id, "type": content_type, "lang": lang}
            )
            db.commit()
        finally:
            db.close()

    def publish(self, race_id: str, content_type: str, lang: str) -> None:
        """Publish content."""
        db = get_db()
        try:
            db.execute(
                text("UPDATE contents SET status = 'published', updated_at = CURRENT_TIMESTAMP WHERE race_id = :race_id AND content_type = :type AND lang = :lang"),
                {"race_id": race_id, "type": content_type, "lang": lang}
            )
            db.commit()
        finally:
            db.close()

    def fetch_by_race_type_lang(self, race_id: str, content_type: str, lang: str) -> Optional[Dict[str, Any]]:
        """Fetch content by race, type, and language."""
        db = get_db()
        try:
            result = db.execute(
                text("SELECT * FROM contents WHERE race_id = :race_id AND content_type = :type AND lang = :lang"),
                {"race_id": race_id, "type": content_type, "lang": lang}
            ).fetchone()
            
            if result:
                return {
                    "id": result[0],
                    "race_id": result[1],
                    "content_type": result[2],
                    "lang": result[3],
                    "status": result[4],
                    "text": result[5],
                    "created_at": result[6],
                    "updated_at": result[7],
                }
            return None
        finally:
            db.close()

    def _upsert(self, race_id: str, content_type: str, lang: str, status: str, text: str) -> None:
        """Internal upsert method."""
        db = get_db()
        try:
            db.execute(
                text("""
                    INSERT OR REPLACE INTO contents (race_id, content_type, lang, status, text, updated_at)
                    VALUES (:race_id, :type, :lang, :status, :text, CURRENT_TIMESTAMP)
                """),
                {
                    "race_id": race_id,
                    "type": content_type,
                    "lang": lang,
                    "status": status,
                    "text": text,
                }
            )
            db.commit()
        finally:
            db.close()


class BingoRepo:
    """Bingo repository."""

    def save_template(self, race_id: str, lang: str, cells: List[Dict]) -> None:
        """Save bingo card template."""
        db = get_db()
        try:
            cells_str = json.dumps(cells)
            db.execute(
                text("""
                    INSERT OR REPLACE INTO bingo_cards (race_id, lang, cells_json)
                    VALUES (:race_id, :lang, :cells)
                """),
                {"race_id": race_id, "lang": lang, "cells": cells_str}
            )
            db.commit()
        finally:
            db.close()

    def get_template(self, race_id: str, lang: str) -> Optional[List[Dict]]:
        """Get bingo card template."""
        db = get_db()
        try:
            result = db.execute(
                text("SELECT cells_json FROM bingo_cards WHERE race_id = :race_id AND lang = :lang"),
                {"race_id": race_id, "lang": lang}
            ).fetchone()
            
            if result:
                return json.loads(result[0])
            return None
        finally:
            db.close()

    def upsert_user_state(self, race_id: str, telegram_id: int, states: Dict[str, str]) -> None:
        """Upsert user's bingo state."""
        db = get_db()
        try:
            states_str = json.dumps(states)
            db.execute(
                text("""
                    INSERT OR REPLACE INTO bingo_user_state (race_id, telegram_id, states_json, updated_at)
                    VALUES (:race_id, :user_id, :states, CURRENT_TIMESTAMP)
                """),
                {"race_id": race_id, "user_id": telegram_id, "states": states_str}
            )
            db.commit()
        finally:
            db.close()

    def get_user_state(self, race_id: str, telegram_id: int) -> Optional[Dict[str, str]]:
        """Get user's bingo state."""
        db = get_db()
        try:
            result = db.execute(
                text("SELECT states_json FROM bingo_user_state WHERE race_id = :race_id AND telegram_id = :user_id"),
                {"race_id": race_id, "user_id": telegram_id}
            ).fetchone()
            
            if result:
                return json.loads(result[0])
            return None
        finally:
            db.close()
