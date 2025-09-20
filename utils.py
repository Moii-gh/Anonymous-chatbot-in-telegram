import asyncio
import logging
from datetime import datetime, timedelta

from aiogram import Bot

import data
from keyboards import get_main_keyboard

async def cleanup_inactive_users(bot: Bot):
    """
    Периодически проверяет и удаляет неактивных пользователей из очереди ожидания.
    """
    while True:
        await asyncio.sleep(60 * 5) # Проверка каждые 5 минут
        now = datetime.now()
        
        for gender, queue in data.waiting_queue.items():
            for user_id in queue[:]:
                # Проверяем, есть ли профиль и время последней активности
                if user_id in data.user_profiles and "last_active" in data.user_profiles[user_id]:
                    last_active_time = data.user_profiles[user_id]["last_active"]
                    
                    # Если неактивен более 15 минут, удаляем из очереди
                    if now - last_active_time > timedelta(minutes=15):
                        queue.remove(user_id)
                        logging.info(f"Removed inactive user {user_id} from queue.")
                        try:
                            await bot.send_message(
                                user_id,
                                "Вы были убраны из очереди поиска из-за неактивности.",
                                reply_markup=get_main_keyboard()
                            )
                        except Exception as e:
                            logging.error(f"Could not notify inactive user {user_id}: {e}")
