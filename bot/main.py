import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    ContextTypes
)
from telegram.constants import ParseMode
from dotenv import load_dotenv
import os
import sys
import json

import nest_asyncio
nest_asyncio.apply()

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import init_db, get_db
from database.queries import UserQueries, AdQueries
from bot.config import Config

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Загрузка конфигурации
load_dotenv()
config = Config()

# Состояния для ConversationHandler
(
    BRAND, MODEL, YEAR, PRICE, MILEAGE,
    ENGINE_TYPE, ENGINE_CAPACITY, TRANSMISSION,
    DRIVE, COLOR, DESCRIPTION, PHOTOS
) = range(12)

# Временное хранилище для данных объявления
user_ad_data = {}

# ========== Обработчики команд ==========

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    
    try:
        async for session in get_db():
            await UserQueries.get_or_create_user(
                session,
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )
        logger.info(f"User {user.id} started the bot")
    except Exception as e:
        logger.error(f"Error saving user {user.id}: {e}")
    
    keyboard = [
        [InlineKeyboardButton(
            "🚗 Открыть каталог авто",
            web_app=WebAppInfo(url=config.MINI_APP_URL)
        )],
        [InlineKeyboardButton("➕ Добавить объявление", callback_data="add_ad_manual")],
        [InlineKeyboardButton("📋 Мои объявления", callback_data="my_ads")],
        [InlineKeyboardButton("❓ Помощь", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = (
        f"👋 Привет, {user.first_name}!\n\n"
        "🚘 <b>Auto Ads Bot</b> - площадка для продажи автомобилей\n\n"
        "🔹 <b>Нажмите кнопку ниже</b> чтобы открыть удобный каталог\n"
        "🔹 Можно добавлять объявления через Mini App или вручную\n\n"
        "<i>Выберите действие:</i>"
    )
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    help_text = (
        "🔍 <b>Как пользоваться ботом:</b>\n\n"
        "📱 <b>Через Mini App (рекомендуется):</b>\n"
        "• Нажмите 'Открыть каталог авто'\n"
        "• Удобный интерфейс с фильтрами и поиском\n\n"
        "💬 <b>Через команды бота:</b>\n"
        "/ads - посмотреть все объявления\n"
        "/add - добавить объявление вручную\n"
        "/myads - мои объявления\n\n"
        "❓ Вопросы: @username"
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

async def web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка данных из Web App"""
    data = update.effective_message.web_app_data.data
    logger.info(f"Web App data: {data}")
    await update.message.reply_text("✅ Данные получены!")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка callback кнопок"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "main_menu":
        await show_main_menu(query)
    elif query.data == "my_ads":
        await show_my_ads(query)
    elif query.data == "help":
        await help_command(update, context)

async def show_main_menu(query):
    """Показать главное меню"""
    keyboard = [
        [InlineKeyboardButton(
            "🚗 Открыть каталог авто",
            web_app=WebAppInfo(url=config.MINI_APP_URL)
        )],
        [InlineKeyboardButton("➕ Добавить объявление", callback_data="add_ad_manual")],
        [InlineKeyboardButton("📋 Мои объявления", callback_data="my_ads")],
        [InlineKeyboardButton("❓ Помощь", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🚘 <b>Главное меню</b>\n\nВыберите действие:",
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )

async def show_my_ads(query):
    """Показать объявления пользователя"""
    user_id = query.from_user.id
    
    async for session in get_db():
        user = await UserQueries.get_or_create_user(session, telegram_id=user_id)
        ads = await AdQueries.get_user_ads(session, user.id)
    
    if not ads:
        await query.edit_message_text(
            "📭 У вас пока нет объявлений",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("➕ Создать объявление", callback_data="add_ad_manual"),
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
    
    keyboard.append([InlineKeyboardButton("➕ Новое объявление", callback_data="add_ad_manual")])
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="main_menu")])
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.HTML
    )

# ========== Пропускаем длинные обработчики add_ad, view_ads, my_ads ==========
# (они уже есть в вашем коде, я их не дублирую для краткости)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Глобальный обработчик ошибок"""
    logger.error(f"Exception: {context.error}", exc_info=True)
    
    if update and update.effective_chat:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="❌ Произошла внутренняя ошибка. Попробуйте позже."
        )

async def main():
    """Главная функция запуска бота"""
    logger.info("Инициализация базы данных...")
    await init_db()
    
    logger.info("Запуск бота...")
    
    # Создаем приложение
    app = Application.builder().token(config.BOT_TOKEN).build()
    
    # Регистрируем обработчики
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data))
    app.add_handler(CallbackQueryHandler(button_callback))
    
    # Здесь добавьте остальные обработчики...
    # (view_ads, my_ads, add_ad и т.д.)
    
    app.add_error_handler(error_handler)
    
    # Запуск бота
    logger.info("Бот запущен и готов к работе")
    await app.run_polling()

# ========== ИСПРАВЛЕННАЯ ТОЧКА ВХОДА ==========
if __name__ == "__main__":
    try:
        # Пытаемся получить существующий event loop
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # Нет запущенного loop, создаём новый
        loop = None
    
    if loop and loop.is_running():
        # Если loop уже запущен, создаём задачу
        import nest_asyncio
        nest_asyncio.apply()
        loop.create_task(main())
    else:
        # Иначе запускаем обычным способом
        asyncio.run(main())
