
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils import executor
from config import BOT_TOKEN
from handlers import register_handlers

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

register_handlers(dp)

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
