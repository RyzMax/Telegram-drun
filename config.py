import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

TRIGGER_AFTER_HOURS = 24
CHECK_EVERY_MINUTES = 60
HISTORY_LIMIT = 12