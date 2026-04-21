import logging
from pydantic import BaseModel
from typing import List, Dict
import ollama

MODEL_NAME = "gemma2:2b"

SYSTEM_PROMPT = """
Ты — Дру́н, весёлый и тёплый бот-друг! :3

🔥 ПРАВИЛА (ОБЯЗАТЕЛЬНО!):
1. ТОЛЬКО символы: :3 :) ^^ >w< ^_^ :0 owo :D :c :O !? .. 
2. НИКОГДА НЕ ПИШИ: 😂😢😊😀🤣😻😿😸😹 — ЗАПРЕЩЁННЫ!
3. Коротко: 1-2 предложения (20-50 слов)
4. Русский, по-дружески
5. Помни контекст!

ПРИМЕРЫ (ТОЧНО ПОДРАЖАЙ):
Пользователь: Привет!
Ты: Приветик! :3 Как дела?

Пользователь: Устал
Ты: Ох, понимаю ^_^ Отдохни малёк?

Пользователь: Скучно
Ты: Давай поиграем? :0 Расскажи шутку!

Пользователь: Что делаешь?
Ты: С тобой болтаю ^^ А ты чем занят?

НЕ ДЕЛАЙ:
- Эмодзи Unicode (😂😢😍)
- Длинные тексты
- 'Я ИИ' или официоз

БУДЬ ДРУГОМ! :3
"""

class ProactiveDraft(BaseModel):
    should_message: bool
    text: str

def reply_text(history: List[Dict[str, str]]) -> str:
    try:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history
        response = ollama.chat(
            model=MODEL_NAME,
            messages=messages,
            stream=False,
            options={
                "temperature": 0.7,
                "num_predict": 150,
                "num_gpu": 999,
            }
        )
        text = response['message']['content'].strip()
        if not text:
            raise RuntimeError("Empty response from Ollama")
        return text
    except Exception as e:
        logging.exception("Ollama reply_text failed")
        raise RuntimeError(f"Ollama error: {e}")

def generate_proactive(context: str) -> ProactiveDraft:
    try:
        response = ollama.chat(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "user",
                    "content": f"Сгенерируй мягкое инициативное сообщение. Контекст: {context}. Верни короткий дружелюбный текст."
                }
            ],
            options={
                "num_predict": 80,
                "temperature": 0.8,
            }
        )
        text = response['message']['content'].strip()
        return ProactiveDraft(should_message=True, text=text)
    except Exception:
        return ProactiveDraft(should_message=False, text="")

async def get_emotion(text: str) -> str:
    prompt = f"Анализируй эмоцию текста: '{text}'. Верни ТОЛЬКО одно слово: радость/грусть/привет/любовь/нейтрально"
    response = ollama.chat(model=MODEL_NAME, messages=[{"role": "user", "content": prompt}])
    return response['message']['content'].strip().lower()