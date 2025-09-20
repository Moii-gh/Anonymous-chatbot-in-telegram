from datetime import datetime
from aiogram import Router, types, F
from aiogram.filters import Command

import data
from keyboards import get_main_keyboard, get_gender_keyboard

router = Router()

def init_user_profile(user_id):
    """Инициализирует профиль и статистику пользователя, если их нет."""
    if user_id not in data.user_profiles:
        data.user_profiles[user_id] = {
            "gender": "",
            "interests": [],
            "age": "",
            "last_active": datetime.now(),
            "setup_complete": False
        }
    if user_id not in data.blocked_pairs:
        data.blocked_pairs[user_id] = []
    if user_id not in data.user_stats:
        data.user_stats[user_id] = {"chats_count": 0, "messages_sent": 0}

@router.message(Command("start"))
async def send_welcome(message: types.Message):
    """Обработчик команды /start."""
    user_id = message.from_user.id
    init_user_profile(user_id)
    
    if not data.user_profiles[user_id].get("setup_complete", False):
        await message.answer(
            f"👋 Привет, {message.from_user.first_name}!\n\n"
            "Добро пожаловать в анонимный чат-бот! 🎭\n\n"
            "Давайте настроим ваш профиль.\n\n"
            "Укажите ваш пол:",
            reply_markup=get_gender_keyboard()
        )
    else:
        await message.answer(
            "С возвращением! 👋\nВыберите действие:",
            reply_markup=get_main_keyboard()
        )

@router.message(F.text == "❓ Помощь")
async def show_help(message: types.Message):
    """Показывает справку по командам бота."""
    help_text = (
        "<b>❓ Справка по боту:</b>\n\n"
        "<b>🔍 Найти собеседника</b> - поиск случайного собеседника\n"
        "<b>❌ Завершить чат</b> - закончить текущий разговор\n"
        "<b>🚫 Заблокировать</b> - заблокировать текущего собеседника\n"
        "<b>🤝 Обменяться контактами</b> - предложить обменяться юзернеймами\n"
        "<b>🎲 Камень-Ножницы-Бумага</b> - сыграть в мини-игру\n"
        "<b>💎 Подарить награду</b> - отправить виртуальный подарок\n"
        "<b>⚙️ Настройки</b> - изменить ваш профиль\n"
        "<b>📊 Статистика</b> - посмотреть вашу статистику"
    )
    await message.answer(help_text, reply_markup=get_main_keyboard())

@router.message(F.text == "⚙️ Настройки")
async def settings(message: types.Message):
    """Начинает процесс смены настроек профиля."""
    user_id = message.from_user.id
    init_user_profile(user_id)
    data.user_profiles[user_id]["setup_complete"] = False
    await message.answer(
        "⚙️ Изменим ваш профиль.\n\nУкажите ваш пол:",
        reply_markup=get_gender_keyboard()
    )

@router.message(F.text == "📊 Статистика")
async def show_stats(message: types.Message):
    """Показывает статистику пользователя."""
    user_id = message.from_user.id
    init_user_profile(user_id) # На случай, если данных еще нет
    stats = data.user_stats[user_id]
    await message.answer(
        f"<b>📊 Ваша статистика:</b>\n\n"
        f"💬 Всего чатов: {stats['chats_count']}\n"
        f"✉️ Отправлено сообщений: {stats['messages_sent']}"
    )
