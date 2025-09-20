# extras.py

from aiogram import Bot, Router, F, types

import data
from keyboards import get_exchange_keyboard, get_game_keyboard
from handlers.chatting import clear_user_states

router = Router()

# --- Обмен контактами ---

@router.message(F.text == "🤝 Обменяться контактами")
async def request_exchange(message: types.Message, bot: Bot):
    """Отправляет запрос на обмен контактами собеседнику."""
    user_id = message.from_user.id
    if user_id not in data.user_pairs:
        await message.answer("Вы не в чате.")
        return

    partner_id = data.user_pairs[user_id]

    if not message.from_user.username:
        await message.answer("У вас не установлен юзернейм (@username) в настройках Telegram. Вы не можете обмениваться контактами.")
        return

    if user_id in data.exchange_requests:
        await message.answer("Вы уже отправили запрос на обмен. Дождитесь ответа.")
        return

    data.exchange_requests[user_id] = partner_id
    await bot.send_message(
        partner_id,
        "Ваш собеседник предлагает обменяться контактами!",
        reply_markup=get_exchange_keyboard(user_id)
    )
    await message.answer("✅ Запрос на обмен контактами отправлен. Ожидайте ответа.")

@router.callback_query(F.data.startswith("exchange_"))
async def handle_exchange_response(callback: types.CallbackQuery, bot: Bot):
    """Обрабатывает ответ на запрос обмена контактами."""
    user_id = callback.from_user.id
    action, requester_id_str = callback.data.split("_")[1:]
    requester_id = int(requester_id_str)

    # Проверяем, что запрос все еще актуален
    if requester_id not in data.exchange_requests or data.exchange_requests.get(requester_id) != user_id:
        await callback.message.edit_text("❌ Этот запрос больше не действителен.")
        await callback.answer()
        return

    # Получаем информацию о пользователях
    try:
        requester_info = await bot.get_chat(requester_id)
        user_info = await bot.get_chat(user_id)
    except Exception as e:
        await callback.message.edit_text("Не удалось получить информацию о пользователях.")
        await callback.answer(f"Ошибка: {e}", show_alert=True)
        return


    if action == "accept":
        if not requester_info.username or not user_info.username:
            await callback.message.edit_text("Не удалось получить юзернейм одного из пользователей. Обмен невозможен.")
            await bot.send_message(requester_id, "Не удалось получить юзернейм одного из пользователей. Обмен невозможен.")
        else:
            await bot.send_message(requester_id, f"✅ Собеседник согласился! Вот его контакт: @{user_info.username}")
            await callback.message.edit_text(f"✅ Вы согласились! Вот контакт собеседника: @{requester_info.username}")
    else:  # decline
        await bot.send_message(requester_id, "❌ Собеседник отклонил ваш запрос на обмен контактами.")
        await callback.message.edit_text("Вы отклонили запрос.")

    # Удаляем запрос после ответа
    if requester_id in data.exchange_requests:
        del data.exchange_requests[requester_id]
        
    await callback.answer()

# --- Камень-Ножницы-Бумага ---

@router.message(F.text == "🎲 Камень-Ножницы-Бумага")
async def start_game(message: types.Message, bot: Bot):
    """Предлагает сыграть в игру."""
    user_id = message.from_user.id
    if user_id not in data.user_pairs:
        await message.answer("Вы не в чате.")
        return

    partner_id = data.user_pairs[user_id]
    
    # Проверяем, не начата ли уже игра
    if user_id in data.active_games:
        await message.answer("Игра уже идет. Сделайте свой ход.", reply_markup=get_game_keyboard())
        return

    data.active_games[user_id] = {"partner_id": partner_id, "move": None}
    data.active_games[partner_id] = {"partner_id": user_id, "move": None}

    await message.answer("Вы предложили игру! Делайте свой ход:", reply_markup=get_game_keyboard())
    await bot.send_message(partner_id, "Собеседник предлагает сыграть в 'Камень-Ножницы-Бумага'! Делайте ход:", reply_markup=get_game_keyboard())

@router.callback_query(F.data.startswith("game_"))
async def make_move(callback: types.CallbackQuery, bot: Bot):
    """Обрабатывает ход игрока."""
    user_id = callback.from_user.id
    move = callback.data.split("_")[1]
    move_map = {"rock": "🗿", "scissors": "✂️", "paper": "📄"}
    move_emoji = move_map.get(move, "")

    if user_id not in data.active_games:
        await callback.message.edit_text("Игра не найдена или уже завершена.")
        await callback.answer()
        return
        
    if data.active_games[user_id]["move"] is not None:
        await callback.answer("Вы уже сделали свой ход. Ожидайте соперника.", show_alert=True)
        return

    data.active_games[user_id]["move"] = move
    await callback.message.edit_text(f"Вы выбрали: {move_emoji}")

    partner_id = data.active_games[user_id]["partner_id"]
    partner_game_state = data.active_games.get(partner_id)

    if partner_game_state and partner_game_state["move"]:
        # Оба игрока сделали ход, определяем результат
        partner_move = partner_game_state["move"]
        result_p1, result_p2 = determine_winner(move, partner_move)

        # Отправляем результаты обоим игрокам
        await bot.send_message(user_id, result_p1)
        await bot.send_message(partner_id, result_p2)

        # Очищаем состояние игры
        if user_id in data.active_games:
            del data.active_games[user_id]
        if partner_id in data.active_games:
            del data.active_games[partner_id]
    else:
        # Ждем хода партнера
        await bot.send_message(partner_id, "Собеседник сделал свой ход. Теперь ваша очередь!")
        await callback.answer("Ваш ход принят. Ждем соперника...")

def determine_winner(p1_move, p2_move):
    """Определяет победителя и возвращает два разных сообщения для каждого игрока."""
    rules = {
        "rock": "scissors",
        "scissors": "paper",
        "paper": "rock"
    }
    
    # Эмодзи для ходов
    move_map = {"rock": "🗿", "scissors": "✂️", "paper": "📄"}
    p1_emoji = move_map[p1_move]
    p2_emoji = move_map[p2_move]
    
    # Заголовки результатов
    header = f"Игра окончена!\n\nВаш ход: {p1_emoji}\nХод соперника: {p2_emoji}\n\n"
    header_reversed = f"Игра окончена!\n\nВаш ход: {p2_emoji}\nХод соперника: {p1_emoji}\n\n"

    if rules[p1_move] == p2_move:
        # Игрок 1 победил
        result_p1 = header + "Вы победили! 🎉"
        result_p2 = header_reversed + "Вы проиграли. 😥"
    elif rules[p2_move] == p1_move:
        # Игрок 2 победил
        result_p1 = header + "Вы проиграли. 😥"
        result_p2 = header_reversed + "Вы победили! 🎉"
    else:
        # Ничья
        result_p1 = result_p2 = header + "Ничья! 🤝"
        
    return result_p1, result_p2