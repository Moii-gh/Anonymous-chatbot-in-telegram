from aiogram import Router, types, F, Bot
from aiogram.exceptions import TelegramBadRequest

import data
import config  # <- Добавлено
from keyboards import get_interests_keyboard, get_main_keyboard
from handlers.common import init_user_profile

router = Router()

@router.message(F.text.in_(["👦 Парень", "👧 Девушка", "🤖 Не указывать"]))
async def set_gender(message: types.Message):
    """Устанавливает пол пользователя и предлагает выбрать интересы."""
    user_id = message.from_user.id
    init_user_profile(user_id)
    
    gender_map = {
        "👦 Парень": "male",
        "👧 Девушка": "female",
        "🤖 Не указывать": "other"
    }
    data.user_profiles[user_id]["gender"] = gender_map[message.text]
    
    await message.answer(
        "Отлично! 👍\n\n"
        "Теперь выберите ваши интересы (можно выбрать несколько):",
        reply_markup=get_interests_keyboard(user_id)
    )

@router.callback_query(F.data.startswith("interest_"))
async def toggle_interest(callback: types.CallbackQuery):
    """Обрабатывает нажатие на кнопку интереса (добавляет/удаляет)."""
    user_id = callback.from_user.id
    init_user_profile(user_id)
    
    interest_id = int(callback.data.split("_")[1])
    interest = config.INTERESTS[interest_id] # <- Исправлено
    
    user_interests = data.user_profiles[user_id]["interests"]
    if interest in user_interests:
        user_interests.remove(interest)
    else:
        user_interests.append(interest)
        
    try:
        await callback.message.edit_reply_markup(
            reply_markup=get_interests_keyboard(user_id)
        )
    except TelegramBadRequest:
        # Игнорируем ошибку, если клавиатура не изменилась
        pass
    await callback.answer()

@router.callback_query(F.data == "interests_done")
async def finish_setup(callback: types.CallbackQuery, bot: Bot):
    """Завершает настройку профиля."""
    user_id = callback.from_user.id
    data.user_profiles[user_id]["setup_complete"] = True
    
    interests_list = data.user_profiles[user_id]["interests"]
    interests_text = ", ".join(interests_list) if interests_list else "не указаны"
    
    gender_text_map = {
        "male": "Парень",
        "female": "Девушка",
        "other": "Не указан"
    }
    gender_text = gender_text_map.get(data.user_profiles[user_id]['gender'], "Не указан")
    
    await callback.message.edit_text(
        f"<b>🎉 Профиль настроен!</b>\n\n"
        f"<b>Пол:</b> {gender_text}\n"
        f"<b>Интересы:</b> {interests_text}\n\n"
        "Теперь вы можете искать собеседников!"
    )
    await bot.send_message(
        user_id,
        "Выберите действие:",
        reply_markup=get_main_keyboard()
    )
    await callback.answer()

