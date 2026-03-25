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

# Импорты из проекта
from database.db import init_db, get_db
from database.queries import UserQueries

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

# Проверка обязательных переменных
if not BOT_TOKEN:
    logger.error("❌ BOT_TOKEN не установлен в переменных окружения!")
    sys.exit(1)

logger.info(f"🚀 Bot starting with token: {BOT_TOKEN[:10]}...")
logger.info(f"🌐 Mini App URL: {MINI_APP_URL}")

# ========== ОБРАБОТЧИКИ КОМАНД ==========

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start - главное меню"""
    user = update.effective_user
    logger.info(f"User {user.id} (@{user.username}) started the bot")
    
    # Сохраняем пользователя в БД
    try:
        async for session in get_db():
            await UserQueries.get_or_create_user(
                session,
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )
        logger.debug(f"User {user.id} saved to database")
    except Exception as e:
        logger.error(f"Error saving user {user.id}: {e}")
    
    # Создаём клавиатуру с Web App кнопкой
    keyboard = [
        [InlineKeyboardButton(
            "🚗 Открыть каталог авто",
            web_app=WebAppInfo(url=MINI_APP_URL)
        )],
        [InlineKeyboardButton("➕ Добавить объявление", callback_data="add_ad")],
        [InlineKeyboardButton("📋 Мои объявления", callback_data="my_ads")],
        [InlineKeyboardButton("❓ Помощь", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = (
        f"👋 <b>Привет, {user.first_name}!</b>\n\n"
        "🚘 <b>Auto Ads Bot</b> - площадка для продажи автомобилей\n\n"
        "🔹 <b>Нажмите кнопку ниже</b> чтобы открыть удобный каталог\n"
        "🔹 Можно добавлять объявления через Mini App или вручную\n"
        "🔹 Все объявления синхронизируются автоматически\n\n"
        "<i>Выберите действие:</i>"
    )
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /help"""
    help_text = (
        "🔍 <b>Как пользоваться ботом:</b>\n\n"
        "📱 <b>Через Mini App (рекомендуется):</b>\n"
        "• Нажмите 'Открыть каталог авто'\n"
        "• Удобный интерфейс с фильтрами и поиском\n"
        "• Можно добавлять фото и смотреть детали\n\n"
        "💬 <b>Через команды бота:</b>\n"
        "• /start - главное меню\n"
        "• /help - эта справка\n"
        "• /ads - посмотреть все объявления\n"
        "• /add - добавить объявление вручную\n"
        "• /myads - мои объявления\n\n"
        "❓ Если возникли вопросы, напишите @autoads_support"
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
    """Обработчик команды /ads - просмотр объявлений"""
    await update.message.reply_text(
        "🔍 Для просмотра объявлений используйте Mini App:\n"
        f"{MINI_APP_URL}\n\n"
        "Или нажмите кнопку 'Открыть каталог авто' в главном меню."
    )


async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /add - добавление объявления"""
    await update.message.reply_text(
        "➕ Для добавления объявления используйте Mini App:\n"
        f"{MINI_APP_URL}/add-ad.html\n\n"
        "Или нажмите кнопку 'Добавить объявление' в главном меню."
    )


async def myads_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /myads - мои объявления"""
    user = update.effective_user
    
    try:
        async for session in get_db():
            db_user = await UserQueries.get_or_create_user(session, telegram_id=user.id)
            ads = await AdQueries.get_user_ads(session, db_user.id)
        
        if not ads:
            await update.message.reply_text(
                "📭 У вас пока нет объявлений\n\n"
                "Чтобы создать объявление, используйте Mini App: "
                f"{MINI_APP_URL}/add-ad.html"
            )
            return
        
        text = "📋 <b>Ваши объявления:</b>\n\n"
        for ad in ads[:5]:
            status = "✅" if ad.is_active else "⏸"
            text += f"{status} <b>{ad.brand} {ad.model}</b> ({ad.year}) - {ad.price:,} ₽\n"
        
        text += f"\n<i>Для управления объявлениями откройте Mini App</i>"
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
        
    except Exception as e:
        logger.error(f"Error in myads_command: {e}")
        await update.message.reply_text("❌ Ошибка при загрузке объявлений")


async def web_app_data_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка данных из Web App"""
    data = update.effective_message.web_app_data.data
    user = update.effective_user
    logger.info(f"Web App data from user {user.id}: {data[:200]}...")
    
    try:
        # Здесь можно обработать данные из Mini App
        # Например, уведомления о новых объявлениях
        await update.message.reply_text(
            "✅ Данные успешно получены! Спасибо за использование Mini App."
        )
    except Exception as e:
        logger.error(f"Error processing web app data: {e}")
        await update.message.reply_text("❌ Ошибка обработки данных")


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка callback кнопок"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    logger.debug(f"Button clicked: {data}")
    
    if data == "main_menu":
        await show_main_menu(query)
    elif data == "my_ads":
        await show_my_ads(query)
    elif data == "add_ad":
        await show_add_ad_info(query)
    elif data == "help":
        await help_command(update, context)
    elif data == "back_to_ads":
        await query.edit_message_text(
            "🔍 Используйте Mini App для просмотра объявлений:\n"
            f"{MINI_APP_URL}"
        )


async def show_main_menu(query) -> None:
    """Показать главное меню"""
    keyboard = [
        [InlineKeyboardButton(
            "🚗 Открыть каталог авто",
            web_app=WebAppInfo(url=MINI_APP_URL)
        )],
        [InlineKeyboardButton("➕ Добавить объявление", callback_data="add_ad")],
        [InlineKeyboardButton("📋 Мои объявления", callback_data="my_ads")],
        [InlineKeyboardButton("❓ Помощь", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🚘 <b>Главное меню</b>\n\nВыберите действие:",
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )


async def show_my_ads(query) -> None:
    """Показать объявления пользователя"""
    user_id = query.from_user.id
    
    try:
        async for session in get_db():
            user = await UserQueries.get_or_create_user(session, telegram_id=user_id)
            ads = await AdQueries.get_user_ads(session, user.id)
        
        if not ads:
            await query.edit_message_text(
                "📭 У вас пока нет объявлений\n\n"
                "Чтобы создать объявление, используйте Mini App: "
                f"{MINI_APP_URL}/add-ad.html",
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


async def show_add_ad_info(query) -> None:
    """Показать информацию о добавлении объявления"""
    await query.edit_message_text(
        "➕ <b>Добавление объявления</b>\n\n"
        "Для добавления объявления используйте Mini App:\n"
        f"{MINI_APP_URL}/add-ad.html\n\n"
        "Или воспользуйтесь ручным добавлением через команду /add",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔗 Открыть форму", web_app=WebAppInfo(url=f"{MINI_APP_URL}/add-ad.html")),
            InlineKeyboardButton("◀️ Назад", callback_data="main_menu")
        ]])
    )


async def error_handler(update: Optional[Update], context: ContextTypes.DEFAULT_TYPE) -> None:
    """Глобальный обработчик ошибок"""
    logger.error(f"Exception: {context.error}", exc_info=True)
    
    if update and update.effective_chat:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="❌ Произошла внутренняя ошибка. Попробуйте позже."
        )


# ========== ОСНОВНАЯ ФУНКЦИЯ ==========

async def main() -> None:
    """Главная функция запуска бота"""
    logger.info("=" * 60)
    logger.info("Auto Ads Bot Starting...")
    logger.info("=" * 60)
    
    # Проверка токена
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN not found in environment!")
        return
    
    # Инициализация базы данных
    logger.info("Initializing database...")
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return
    
    # Создание приложения
    logger.info("Building application...")
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Регистрация обработчиков команд
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("ads", ads_command))
    app.add_handler(CommandHandler("add", add_command))
    app.add_handler(CommandHandler("myads", myads_command))
    
    # Web App data handler
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data_handler))
    
    # Callback handlers
    app.add_handler(CallbackQueryHandler(button_callback))
    
    # Обработчик ошибок
    app.add_error_handler(error_handler)
    
    # Запуск бота
    logger.info("🚀 Bot is ready! Starting polling...")
    logger.info(f"🌐 Mini App URL: {MINI_APP_URL}")
    logger.info("=" * 60)
    
    await app.run_polling()


# ========== ТОЧКА ВХОДА ==========

def run() -> None:
    """Запуск бота в отдельном event loop"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
    finally:
        loop.close()


if __name__ == "__main__":
    run()
