# Telegram-drun
Ваш "друг" живущий на компьютере

<h1>Requirements</h1>

- Python 3.13

- Gemma 2 2B

- 16 GB RAN

- ollama

<h1>Start:</h1>
В .env вписывайте свой бот токен

```shell
git clone https://github.com/RyzMax/telegram-drun
cd telegram-drun

ollama serve
ollama pull gemma2:2b

python bot.py
```
