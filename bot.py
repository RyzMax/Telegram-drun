import os
import asyncio
import logging
from datetime import datetime, timezone, timedelta
import aiosqlite
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from ai import reply_text, generate_proactive, get_emotion
from db import init_db, touch_user, get_due_users, mark_proactive, set_proactive_enabled, add_message, \
    get_recent_messages

load_dotenv()
logging.basicConfig(level=logging.INFO)

bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()
router = Router()
dp.include_router(router)

TRIGGER_AFTER_HOURS = 24
CHECK_EVERY_MINUTES = 60
HISTORY_LIMIT = 12


@router.message(CommandStart())
async def start(message: Message):
    await touch_user(message.chat.id)
    await message.answer("Привет! Я твой локальный AI-друг на Ollama. Пиши!")


@router.message(Command("stop"))
async def stop_proactive(message: Message):
    await set_proactive_enabled(message.chat.id, False)
    await message.answer("Ок, я больше не буду писать первым.")


@router.message(Command("resume"))
async def resume_proactive(message: Message):
    await set_proactive_enabled(message.chat.id, True)
    await message.answer("Хорошо, я снова могу иногда начинать разговор.")


@router.message(F.text)
async def on_text(message: Message):
    chat_id = message.chat.id
    text = message.text
    STICKERS = {
        "радость": "CAACAgIAAxkBAAFHvYNp56JZPRhrIN_g5AYVx6weQfZ4jAACgkwAAhWvkElOeAEMbTSTHDsE",
        "грусть": "CAACAgIAAxkBAAFHvX9p56JDqcbdb9B0-6smRiZIG6n4xAACUEUAAvi0kUm8aDxWMF043zsE",
        "привет": "CAACAgIAAxkBAAFHvXlp56IyPU97PcmDPW7BgFFyb-IT_AAC3E8AAsF6mUmJJSD86GNA8TsE",
        "любовь": "CAACAgIAAxkBAAFHvWNp56GXDRG_993ZrUIUIbDw7GIE1QACVBYAAnHMfRhFzhH-9EOQbjsE",
        "нейтрально": "CAACAgIAAxkBAAFHvUtp56DiiecB5KedqWgijkp0DRAQYAAC5E0AAv5YQUgmBc27F-Q20jsE"
    }

    logging.info(f"Message from {chat_id}: {text}")

    await touch_user(chat_id)
    await add_message(chat_id, "user", text)

    history = await get_recent_messages(chat_id, HISTORY_LIMIT)
    try:
        answer = await asyncio.to_thread(reply_text, history)
        await add_message(chat_id, "assistant", answer)
        await message.answer(answer)
    except Exception as e:
        logging.exception("Bot handler failed")
        await message.answer(f"AI недоступен: {e}")

    answer = reply_text(history)


    emotion = await get_emotion(answer)


    if emotion in STICKERS:
        await bot.send_sticker(message.chat.id, STICKERS[emotion])


async def proactive_job():
    due_users = await get_due_users(TRIGGER_AFTER_HOURS)
    logging.info(f"Proactive check: {len(due_users)} users due")

    for chat_id in due_users:
        context = "Пользователь давно не писал. Сообщение должно быть мягким и ненавязчивым."
        try:
            draft = await asyncio.to_thread(generate_proactive, context)
            if draft.should_message and draft.text.strip():
                await bot.send_message(chat_id, draft.text.strip())
                await mark_proactive(chat_id)
                logging.info(f"Proactive message sent to {chat_id}")
        except Exception as e:
            logging.exception(f"Proactive failed for {chat_id}")


async def main():
    await init_db()

    scheduler = AsyncIOScheduler()
    scheduler.add_job(proactive_job, "interval", minutes=CHECK_EVERY_MINUTES)
    scheduler.start()

    logging.info("Bot starting...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())