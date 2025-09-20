from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from config import INTERESTS
import data # Импортируем data для доступа к user_profiles

def get_gender_keyboard():
    """Возвращает клавиатуру для выбора пола."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👦 Парень"), KeyboardButton(text="👧 Девушка")],
            [KeyboardButton(text="🤖 Не указывать")]
        ], resize_keyboard=True, one_time_keyboard=True
    )

def get_main_keyboard():
    """Возвращает главную клавиатуру меню."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔍 Найти собеседника")],
            [KeyboardButton(text="⚙️ Настройки"), KeyboardButton(text="📊 Статистика")],
            [KeyboardButton(text="❓ Помощь")]
        ], resize_keyboard=True
    )

def get_chat_keyboard():
    """Возвращает клавиатуру для активного чата."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❌ Завершить чат"), KeyboardButton(text="🚫 Заблокировать")],
            [KeyboardButton(text="🤝 Обменяться контактами"), KeyboardButton(text="🎲 Камень-Ножницы-Бумага")],
            [KeyboardButton(text="💎 Подарить награду")]
        ],
        resize_keyboard=True
    )

def get_interests_keyboard(user_id):
    """
    Возвращает инлайн-клавиатуру для выбора интересов,
    отмечая уже выбранные.
    """
    buttons = []
    user_interests = data.user_profiles.get(user_id, {}).get("interests", [])
    
    # Создаем ряды кнопок по две в каждом
    for i in range(0, len(INTERESTS), 2):
        row = []
        # Первая кнопка в ряду
        interest_text_1 = INTERESTS[i]
        if interest_text_1 in user_interests:
            interest_text_1 += " ✅"
        row.append(InlineKeyboardButton(text=interest_text_1, callback_data=f"interest_{i}"))

        # Вторая кнопка в ряду, если есть
        if i + 1 < len(INTERESTS):
            interest_text_2 = INTERESTS[i + 1]
            if interest_text_2 in user_interests:
                interest_text_2 += " ✅"
            row.append(InlineKeyboardButton(text=interest_text_2, callback_data=f"interest_{i+1}"))
        buttons.append(row)
        
    buttons.append([InlineKeyboardButton(text="✅ Готово", callback_data="interests_done")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_exchange_keyboard(requester_id):
    """Возвращает клавиатуру для подтверждения обмена контактами."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Принять", callback_data=f"exchange_accept_{requester_id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"exchange_decline_{requester_id}")
        ]
    ])

def get_game_keyboard():
    """Возвращает клавиатуру для игры 'Камень-Ножницы-Бумага'."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🗿", callback_data="game_rock"),
            InlineKeyboardButton(text="✂️", callback_data="game_scissors"),
            InlineKeyboardButton(text="📄", callback_data="game_paper")
        ]
    ])
