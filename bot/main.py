"""
Auto Ads Bot - Telegram бот для продажи автомобилей
"""
import logging
import asyncio
import os
import sys
from typing import Optional

from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes
)
from telegram.constants import ParseMode

# Добавляем корень проекта в путь для импортов
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import init_db, get_db
from database.queries import UserQueries, AdQueries

# Загрузка переменных окружения
load_dotenv()

# ========== НАСТРОЙКА ЛОГИРОВАНИЯ ==========
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ========== КОНФИГУРАЦИЯ ==========
BOT_TOKEN = os.getenv('BOT_TOKEN')
MINI_APP_URL = os.getenv('MINI_APP_URL', 'http://localhost')
ADMIN_IDS = [int(id) for id in os.getenv('ADMIN_IDS', '').split(',') if id]

if not BOT_TOKEN:
    logger.error("BOT_TOKEN is not set in environment variables!")
    sys.exit(1)

logger.info(f"Bot starting with token: {BOT_TOKEN[:10]}...")
logger.info(f"Mini App URL: {MINI_APP_URL}")

# ========== ОБРАБОТЧИКИ ==========

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    logger.info(f"User {user.id} (@{user.username}) started the bot")
    try:
        async for session in get_db():
            await UserQueries.get_or_create_user(
                session,
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )
    except Exception as e:
        logger.error(f"Error saving user {user.id}: {e}")

    keyboard = [
        [InlineKeyboardButton("🚗 Открыть каталог", web_app=WebAppInfo(url=MINI_APP_URL))],
        [InlineKeyboardButton("➕ Добавить", callback_data="add_ad")],
        [InlineKeyboardButton("📋 Мои", callback_data="my_ads")],
        [InlineKeyboardButton("❓ Помощь", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"👋 Привет, {user.first_name}!\n\n"
        "🚘 Auto Ads Bot готов к работе!\n\n"
        "Нажмите кнопку 'Открыть каталог' для просмотра объявлений.",
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    help_text = (
        "🔍 <b>Помощь</b>\n\n"
        "/start - Главное меню\n"
        "/help - Эта справка\n\n"
        "Для просмотра объявлений используйте кнопку 'Открыть каталог'."
    )
    if update.callback_query:
        await update.callback_query.edit_message_text(
            help_text,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("◀️ Назад", callback_data="main_menu")
            ]])
        )
    else:
        await update.message.reply_text(help_text, parse_mode=ParseMode.HTML)

async def ads_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "🔍 Для просмотра объявлений используйте Mini App:\n"
        f"{MINI_APP_URL}\n\n"
        "Или нажмите кнопку 'Открыть каталог' в главном меню."
    )

async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "➕ Для добавления объявления используйте Mini App:\n"
        f"{MINI_APP_URL}/add-ad.html\n\n"
        "Или нажмите кнопку 'Добавить' в главном меню."
    )

async def myads_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    try:
        async for session in get_db():
            db_user = await UserQueries.get_or_create_user(session, telegram_id=user.id)
            ads = await AdQueries.get_user_ads(session, db_user.id)

        if not ads:
            await update.message.reply_text(
                "📭 У вас пока нет объявлений.\n\n"
                "Чтобы создать объявление, используйте Mini App:\n"
                f"{MINI_APP_URL}/add-ad.html"
            )
            return

        text = "📋 <b>Ваши объявления:</b>\n\n"
        for ad in ads[:5]:
            status = "✅" if ad.is_active else "⏸"
            text += f"{status} <b>{ad.brand} {ad.model}</b> ({ad.year}) - {ad.price:,} ₽\n"
        text += f"\n<i>Для управления откройте Mini App</i>"
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error(f"Error in myads_command: {e}")
        await update.message.reply_text("❌ Ошибка при загрузке объявлений")

async def web_app_data_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    data = update.effective_message.web_app_data.data
    user = update.effective_user
    logger.info(f"Web App data from user {user.id}: {data[:200]}...")
    await update.message.reply_text("✅ Данные получены!")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == "main_menu":
        await show_main_menu(query)
    elif data == "my_ads":
        await show_my_ads(query)
    elif data == "add_ad":
        await show_add_ad_info(query)
    elif data == "help":
        await help_command(update, context)

async def show_main_menu(query):
    keyboard = [
        [InlineKeyboardButton("🚗 Каталог", web_app=WebAppInfo(url=MINI_APP_URL))],
        [InlineKeyboardButton("➕ Добавить", callback_data="add_ad")],
        [InlineKeyboardButton("📋 Мои", callback_data="my_ads")],
        [InlineKeyboardButton("❓ Помощь", callback_data="help")]
    ]
    await query.edit_message_text(
        "🚘 Главное меню",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_my_ads(query):
    user_id = query.from_user.id
    try:
        async for session in get_db():
            user = await UserQueries.get_or_create_user(session, telegram_id=user_id)
            ads = await AdQueries.get_user_ads(session, user.id)

        if not ads:
            await query.edit_message_text(
                "📭 У вас пока нет объявлений.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("➕ Создать", callback_data="add_ad"),
                    InlineKeyboardButton("◀️ Назад", callback_data="main_menu")
                ]])
            )
            return

        text = "📋 <b>Ваши объявления:</b>\n\n"
        keyboard = []
        for ad in ads[:5]:
            status = "✅" if ad.is_active else "⏸"
            text += f"{status} <b>{ad.brand} {ad.model}</b> ({ad.year}) - {ad.price:,} ₽\n"
            keyboard.append([InlineKeyboardButton(
                f"✏️ {ad.brand} {ad.model}",
                callback_data=f"edit_{ad.id}"
            )])
        keyboard.append([InlineKeyboardButton("➕ Новое", callback_data="add_ad")])
        keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="main_menu")])

        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        logger.error(f"Error showing my ads: {e}")
        await query.edit_message_text("❌ Ошибка при загрузке объявлений")

async def show_add_ad_info(query):
    await query.edit_message_text(
        "➕ <b>Добавление объявления</b>\n\n"
        "Используйте Mini App:\n"
        f"{MINI_APP_URL}/add-ad.html\n\n"
        "Или команду /add",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔗 Открыть форму", web_app=WebAppInfo(url=f"{MINI_APP_URL}/add-ad.html")),
            InlineKeyboardButton("◀️ Назад", callback_data="main_menu")
        ]])
    )

async def error_handler(update: Optional[Update], context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(f"Exception: {context.error}", exc_info=True)
    if update and update.effective_chat:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="❌ Произошла ошибка. Попробуйте позже."
        )

# ========== ОСНОВНАЯ ФУНКЦИЯ ==========

async def main() -> None:
    logger.info("Initializing database...")
    await init_db()

    logger.info("Building application...")
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("ads", ads_command))
    app.add_handler(CommandHandler("add", add_command))
    app.add_handler(CommandHandler("myads", myads_command))

    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data_handler))
    app.add_handler(CallbackQueryHandler(button_callback))

    app.add_error_handler(error_handler)

    logger.info("Bot is ready! Starting polling...")
    await app.run_polling()

# ========== ТОЧКА ВХОДА ==========
if __name__ == "__main__":
    # Простой и надёжный запуск
    asyncio.run(main())
