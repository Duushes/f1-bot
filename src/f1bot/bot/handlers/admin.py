"""Admin handlers."""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler

from f1bot.config import settings
from f1bot.logging import get_logger
from f1bot.storage.repositories import ContentRepo, UserRepo
from f1bot.storage.db import get_db
from sqlalchemy import text

logger = get_logger(__name__)


def is_admin(user_id: int) -> bool:
    """Check if user is admin."""
    return user_id in settings.admin_ids


async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /admin command."""
    user_id = update.effective_user.id

    if not is_admin(user_id):
        await update.message.reply_text("У вас нет прав администратора.")
        return

    # Show admin menu
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 Pending Pre-Race", callback_data="admin:list:pre_race")],
        [InlineKeyboardButton("🏁 Pending Post-Race", callback_data="admin:list:post_race")],
        [InlineKeyboardButton("🔄 Generate Post-Race", callback_data="admin:generate:post_race")],
    ])
    
    await update.message.reply_text("Админ-панель:", reply_markup=keyboard)


async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle admin callbacks."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await query.edit_message_text("У вас нет прав администратора.")
        return
    
    parts = query.data.split(":")
    action = parts[1]
    
    if action == "approve":
        content_type = parts[2]  # pre_race or post_race
        race_id = parts[3]
        lang = parts[4]
        
        content_repo = ContentRepo()
        content_repo.approve(race_id, content_type, lang)
        content_repo.publish(race_id, content_type, lang)
        
        # Publish to users
        await publish_content_to_users(race_id, content_type, lang)
        
        await query.edit_message_text(f"✅ Content approved and published!")
        
    elif action == "cancel":
        content_type = parts[2]
        race_id = parts[3]
        lang = parts[4]
        
        content_repo = ContentRepo()
        # Delete or mark as cancelled
        db = get_db()
        try:
            db.execute(
                text("DELETE FROM contents WHERE race_id = :race_id AND content_type = :type AND lang = :lang"),
                {"race_id": race_id, "type": content_type, "lang": lang}
            )
            db.commit()
        finally:
            db.close()
        
        await query.edit_message_text("❌ Content cancelled")
        
    elif action == "list":
        content_type = parts[2]
        await show_pending_content(update, context, content_type)
        
    elif action == "generate":
        content_type = parts[2]
        if content_type == "post_race":
            from f1bot.jobs.post_race import post_race_job
            await post_race_job()
            await query.edit_message_text("🔄 Post-race generation triggered")


async def show_pending_content(update: Update, context: ContextTypes.DEFAULT_TYPE, content_type: str) -> None:
    """Show pending content list."""
    db = get_db()
    try:
        results = db.execute(
            text("SELECT race_id, lang, text FROM contents WHERE content_type = :type AND status = 'pending_admin' LIMIT 10"),
            {"type": content_type}
        ).fetchall()
        
        if not results:
            await update.callback_query.edit_message_text("No pending content")
            return
        
        text_msg = f"Pending {content_type} content:\n\n"
        keyboard_buttons = []
        
        for race_id, lang, text_content in results:
            text_msg += f"{race_id} ({lang})\n"
            keyboard_buttons.append([
                InlineKeyboardButton(
                    f"✅ {race_id} ({lang})",
                    callback_data=f"admin:approve:{content_type}:{race_id}:{lang}"
                ),
                InlineKeyboardButton(
                    f"❌ {race_id} ({lang})",
                    callback_data=f"admin:cancel:{content_type}:{race_id}:{lang}"
                ),
            ])
        
        keyboard = InlineKeyboardMarkup(keyboard_buttons)
        await update.callback_query.edit_message_text(text_msg, reply_markup=keyboard)
    finally:
        db.close()


async def publish_content_to_users(race_id: str, content_type: str, lang: str) -> None:
    """Publish content to all users with matching language."""
    from f1bot.bot.app import create_application
    from f1bot.storage.repositories import ContentRepo, UserRepo
    
    try:
        application = create_application()
        content_repo = ContentRepo()
        user_repo = UserRepo()
        
        content = content_repo.fetch_by_race_type_lang(race_id, content_type, lang)
        if not content:
            return
        
        # Get all users with this language
        db = get_db()
        try:
            users = db.execute(
                text("SELECT telegram_id FROM users WHERE lang = :lang"),
                {"lang": lang}
            ).fetchall()
            
            text_msg = content["text"]
            
            # Add CTA button
            if content_type == "pre_race":
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🎯 Открыть Bingo Cards" if lang == "ru" else "🎯 Open Bingo Cards", callback_data="menu:bingo")]
                ])
            elif content_type == "post_race":
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("📋 Следующая гонка" if lang == "ru" else "📋 Next Race", callback_data="menu:pre_race")]
                ])
            else:
                keyboard = None
            
            sent = 0
            for (user_id,) in users:
                try:
                    await application.bot.send_message(
                        chat_id=user_id,
                        text=text_msg,
                        reply_markup=keyboard,
                    )
                    sent += 1
                except Exception as e:
                    logger.error(f"Failed to send to user {user_id}: {e}")
            
            logger.info(f"Published {content_type} content to {sent} users")
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error publishing content: {e}")


def register_admin_handlers(application) -> None:
    """Register admin handlers."""
    application.add_handler(CommandHandler("admin", admin_command))
    application.add_handler(CallbackQueryHandler(admin_callback, pattern="^admin:"))
