import random
import logging
from datetime import datetime

from aiogram import Bot, Router, F, types
from aiogram.types import MessageReactionUpdated

import data
from keyboards import get_chat_keyboard, get_main_keyboard
from handlers.common import init_user_profile

router = Router()

@router.message(F.text == "🔍 Найти собеседника")
async def find_partner(message: types.Message, bot: Bot):
    """Ищет собеседника для пользователя."""
    user_id = message.from_user.id
    init_user_profile(user_id)
    
    if not data.user_profiles[user_id].get("setup_complete", False):
        await message.answer("Сначала завершите настройку профиля командой /start")
        return
        
    if user_id in data.user_pairs:
        await message.answer("❗ Вы уже в чате! Завершите текущий разговор.", reply_markup=get_chat_keyboard())
        return

    if user_id in [uid for queue in data.waiting_queue.values() for uid in queue]:
        await message.answer("Вы уже в очереди. Пожалуйста, подождите.")
        return

    user_gender = data.user_profiles[user_id]["gender"]
    user_interests = set(data.user_profiles[user_id]["interests"])
    best_match = None
    best_score = -1

    # Поиск наилучшего совпадения
    for queue_gender in data.waiting_queue:
        for waiting_user in data.waiting_queue[queue_gender][:]:
            if waiting_user == user_id or waiting_user in data.blocked_pairs.get(user_id, []):
                continue
            
            waiting_interests = set(data.user_profiles[waiting_user]["interests"])
            common_interests = len(user_interests.intersection(waiting_interests))
            
            if common_interests > best_score:
                best_score = common_interests
                best_match = waiting_user

    if best_match:
        partner_gender = data.user_profiles[best_match]["gender"]
        data.waiting_queue[partner_gender].remove(best_match)
        
        data.user_pairs[user_id] = best_match
        data.user_pairs[best_match] = user_id
        
        data.user_stats[user_id]["chats_count"] += 1
        data.user_stats[best_match]["chats_count"] += 1
        
        common = user_interests.intersection(set(data.user_profiles[best_match]["interests"]))
        common_text = f"\n🎯 <b>Общие интересы:</b> {', '.join(common)}" if common else ""
        
        await bot.send_message(best_match, f"✨ Собеседник найден!{common_text}\n\nПоздоровайтесь! 👋", reply_markup=get_chat_keyboard())
        await message.answer(f"✨ Собеседник найден!{common_text}\n\nПоздоровайтесь! 👋", reply_markup=get_chat_keyboard())
    else:
        if user_id not in data.waiting_queue[user_gender]:
            data.waiting_queue[user_gender].append(user_id)
        await message.answer("🔍 Ищем собеседника...\nЕсли захотите остановить поиск, нажмите '❌ Завершить чат'.")


def clear_user_states(user_id, partner_id):
    """Очищает все состояния, связанные с чатом, для пары пользователей."""
    for u_id in [user_id, partner_id]:
        if u_id in data.user_pairs: del data.user_pairs[u_id]
        if u_id in data.exchange_requests: del data.exchange_requests[u_id]
        if u_id in data.active_games: del data.active_games[u_id]
        if u_id in data.message_map: del data.message_map[u_id]


@router.message(F.text == "❌ Завершить чат")
async def disconnect_users(message: types.Message, bot: Bot):
    """Завершает чат или отменяет поиск собеседника."""
    user_id = message.from_user.id

    # Удаление из очереди ожидания, если пользователь там
    for queue in data.waiting_queue.values():
        if user_id in queue:
            queue.remove(user_id)
            await message.answer("Поиск отменен.", reply_markup=get_main_keyboard())
            return
    
    # Завершение активного чата
    if user_id in data.user_pairs:
        partner_id = data.user_pairs[user_id]
        await bot.send_message(partner_id, "💔 Собеседник завершил чат.", reply_markup=get_main_keyboard())
        clear_user_states(user_id, partner_id)
        await message.answer("Чат завершен.", reply_markup=get_main_keyboard())
    else:
        await message.answer("Вы не в чате и не в поиске.", reply_markup=get_main_keyboard())

@router.message(F.text == "🚫 Заблокировать")
async def block_user(message: types.Message, bot: Bot):
    """Блокирует собеседника и завершает чат."""
    user_id = message.from_user.id
    if user_id not in data.user_pairs:
        await message.answer("Вы не в чате.", reply_markup=get_main_keyboard())
        return
        
    partner_id = data.user_pairs[user_id]
    data.blocked_pairs.setdefault(user_id, []).append(partner_id)
    
    await bot.send_message(partner_id, "💔 Собеседник завершил и заблокировал чат.", reply_markup=get_main_keyboard())
    clear_user_states(user_id, partner_id)
    await message.answer("🚫 Пользователь заблокирован, чат завершен.", reply_markup=get_main_keyboard())

@router.message(F.text == "💎 Подарить награду")
async def give_reward(message: types.Message, bot: Bot):
    """Отправляет случайную награду собеседнику."""
    user_id = message.from_user.id
    if user_id not in data.user_pairs:
        await message.answer("Вы не в чате.", reply_markup=get_chat_keyboard())
        return
        
    partner_id = data.user_pairs[user_id]
    rewards = ["🎁", "⭐", "💖", "👑", "🏆", "🌟", "💎", "🎉"]
    reward = random.choice(rewards)
    
    await bot.send_message(partner_id, f"🎉 Ваш собеседник подарил вам награду: {reward}")
    await message.answer(f"💝 Награда {reward} отправлена!")

@router.message_reaction()
async def handle_reaction(reaction: MessageReactionUpdated, bot: Bot):
    """Обрабатывает реакции на сообщения и пересылает их собеседнику."""
    user_id = reaction.user.id
    
    if user_id not in data.user_pairs or reaction.chat.id != user_id:
        return
    
    partner_id = data.user_pairs[user_id]
    original_message_id = reaction.message_id
    
    partner_message_id = data.message_map.get(user_id, {}).get(original_message_id)
    
    if partner_message_id:
        try:
            await bot.set_message_reaction(
                chat_id=partner_id,
                message_id=partner_message_id,
                reaction=reaction.new_reaction,
                is_big=False
            )
        except Exception as e:
            logging.error(f"Failed to set reaction for user {partner_id}: {e}")

@router.message(F.content_type.in_({"text", "photo", "animation", "sticker", "voice", "video_note", "document", "video", "audio"}))
async def forward_message(message: types.Message, bot: Bot):
    """Пересылает сообщение от одного пользователя другому в активном чате."""
    user_id = message.from_user.id
    
    # Проверяем, находится ли пользователь в чате
    if user_id not in data.user_pairs:
        # Проверяем, не является ли сообщение командой с основной клавиатуры
        main_keyboard_commands = ["🔍 Найти собеседника", "⚙️ Настройки", "📊 Статистика", "❓ Помощь"]
        if message.text not in main_keyboard_commands:
            await message.answer("Вы не в чате. Используйте '🔍 Найти собеседника'", reply_markup=get_main_keyboard())
        return

    partner_id = data.user_pairs[user_id]
    data.user_stats[user_id]["messages_sent"] += 1
    data.user_profiles[user_id]["last_active"] = datetime.now()
    sent_message = None

    try:
        # Пересылка контента в зависимости от его типа
        if message.text:
            sent_message = await bot.send_message(partner_id, message.text)
        elif message.photo:
            sent_message = await bot.send_photo(partner_id, message.photo[-1].file_id, caption=message.caption)
        elif message.sticker:
            sent_message = await bot.send_sticker(partner_id, message.sticker.file_id)
        elif message.animation:
            sent_message = await bot.send_animation(partner_id, message.animation.file_id, caption=message.caption)
        elif message.voice:
            sent_message = await bot.send_voice(partner_id, message.voice.file_id, caption=message.caption)
        elif message.video_note:
            sent_message = await bot.send_video_note(partner_id, message.video_note.file_id)
        elif message.document:
            sent_message = await bot.send_document(partner_id, message.document.file_id, caption=message.caption)
        elif message.video:
            sent_message = await bot.send_video(partner_id, message.video.file_id, caption=message.caption)
        elif message.audio:
            sent_message = await bot.send_audio(partner_id, message.audio.file_id, caption=message.caption)

        # Сохраняем ID сообщений для синхронизации реакций
        if sent_message:
            data.message_map.setdefault(user_id, {})[message.message_id] = sent_message.message_id
            data.message_map.setdefault(partner_id, {})[sent_message.message_id] = message.message_id

    except Exception as e:
        await message.answer("❌ Ошибка отправки сообщения. Возможно, собеседник заблокировал бота.")
        logging.error(f"Message forward error from {user_id} to {partner_id}: {e}")
