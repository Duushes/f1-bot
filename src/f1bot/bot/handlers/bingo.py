"""Bingo cards handlers."""

import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler

from f1bot.logging import get_logger
from f1bot.storage.repositories import UserRepo, RaceRepo, BingoRepo
from f1bot.services.i18n import t

logger = get_logger(__name__)


def create_bingo_keyboard(cells: list, states: dict, lang: str) -> InlineKeyboardMarkup:
    """Create 4x4 bingo keyboard."""
    keyboard = []
    for i in range(0, 16, 4):
        row = []
        for j in range(4):
            cell_idx = i + j
            if cell_idx < len(cells):
                cell = cells[cell_idx]
                cell_id = cell["id"]
                status = states.get(cell_id, "")
                
                # Emoji based on status
                if status == "checked":
                    emoji = "✅"
                elif status == "verified":
                    emoji = "✅"
                else:
                    emoji = "⬜"
                
                # Truncate title if too long
                title = cell["title"]
                if len(title) > 15:
                    title = title[:12] + "..."
                
                row.append(InlineKeyboardButton(
                    f"{emoji} {title}",
                    callback_data=f"bingo:toggle:{cell_id}"
                ))
        keyboard.append(row)
    
    # Add finish button
    checked_count = sum(1 for s in states.values() if s in ["checked", "verified"])
    finish_text = t("bingo.finish", lang).format(count=checked_count, total=16)
    keyboard.append([InlineKeyboardButton(finish_text, callback_data="bingo:finish")])
    
    return InlineKeyboardMarkup(keyboard)


async def show_bingo_card(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show bingo card for current race."""
    user_id = update.effective_user.id
    user_repo = UserRepo()
    user = user_repo.get(user_id)
    lang = user.get("lang", "ru") if user else "ru"
    
    # Get next race
    race_repo = RaceRepo()
    race = race_repo.get_next_race()
    
    if not race:
        text = t("bingo.no_race", lang)
        if update.callback_query:
            await update.callback_query.edit_message_text(text)
        else:
            await update.message.reply_text(text)
        return
    
    race_id = race["race_id"]
    bingo_repo = BingoRepo()
    
    # Get or create bingo template
    cells = bingo_repo.get_template(race_id, lang)
    if not cells:
        # Generate bingo cells
        from f1bot.services.bingo import generate_bingo_cells
        cells = generate_bingo_cells(race, {}, lang)
        bingo_repo.save_template(race_id, lang, cells)
    
    # Get user state
    states = bingo_repo.get_user_state(race_id, user_id) or {}
    
    # Create keyboard
    keyboard = create_bingo_keyboard(cells, states, lang)
    
    text = t("bingo.title", lang).format(race_name=race["name"])
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=keyboard)
    else:
        await update.message.reply_text(text, reply_markup=keyboard)


async def bingo_toggle_cell(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Toggle bingo cell state."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    cell_id = query.data.split(":")[2]  # bingo:toggle:cell_id
    
    user_repo = UserRepo()
    user = user_repo.get(user_id)
    lang = user.get("lang", "ru") if user else "ru"
    
    # Get next race
    race_repo = RaceRepo()
    race = race_repo.get_next_race()
    
    if not race:
        return
    
    race_id = race["race_id"]
    bingo_repo = BingoRepo()
    
    # Get current state
    states = bingo_repo.get_user_state(race_id, user_id) or {}
    
    # Toggle cell
    current_status = states.get(cell_id, "")
    if current_status in ["checked", "verified"]:
        states[cell_id] = ""
    else:
        states[cell_id] = "checked"
    
    # Save state
    bingo_repo.upsert_user_state(race_id, user_id, states)
    
    # Get cells and update keyboard
    cells = bingo_repo.get_template(race_id, lang)
    if cells:
        keyboard = create_bingo_keyboard(cells, states, lang)
        text = t("bingo.title", lang).format(race_name=race["name"])
        await query.edit_message_text(text, reply_markup=keyboard)


async def bingo_finish(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show bingo finish screen."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    user_repo = UserRepo()
    user = user_repo.get(user_id)
    lang = user.get("lang", "ru") if user else "ru"
    
    # Get next race
    race_repo = RaceRepo()
    race = race_repo.get_next_race()
    
    if not race:
        return
    
    race_id = race["race_id"]
    bingo_repo = BingoRepo()
    
    # Get state
    states = bingo_repo.get_user_state(race_id, user_id) or {}
    checked_count = sum(1 for s in states.values() if s in ["checked", "verified"])
    
    text = t("bingo.finish_result", lang).format(
        checked=checked_count,
        total=16,
        race_name=race["name"]
    )
    
    # Back button
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(t("menu.back", lang), callback_data="menu:main")]
    ])
    
    await query.edit_message_text(text, reply_markup=keyboard)


async def bingo_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle bingo-related callbacks."""
    query = update.callback_query
    await query.answer()
    
    action = query.data.split(":")[1]  # bingo:action
    
    if action == "toggle":
        await bingo_toggle_cell(update, context)
    elif action == "finish":
        await bingo_finish(update, context)
    else:
        await show_bingo_card(update, context)


def register_bingo_handlers(application) -> None:
    """Register bingo handlers."""
    application.add_handler(CallbackQueryHandler(bingo_callback, pattern="^bingo:"))
