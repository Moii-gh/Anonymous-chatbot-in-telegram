import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
import config
from handlers import common, profile_setup, chatting, extras
from utils import cleanup_inactive_users

async def main():
    """
    Основная функция для инициализации и запуска бота.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    )

    bot = Bot(
        token=config.API_TOKEN,
        default=DefaultBotProperties(parse_mode="HTML")
    )
    dp = Dispatcher()

    # Включение роутеров из разных модулей
    logging.info("Including routers...")
    dp.include_router(common.router)
    dp.include_router(profile_setup.router)
    dp.include_router(extras.router)
    dp.include_router(chatting.router)

    asyncio.create_task(cleanup_inactive_users(bot))

    await bot.delete_webhook(drop_pending_updates=True)
    logging.info("Starting polling...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped!")

