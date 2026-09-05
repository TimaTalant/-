import os
import threading
from flask import Flask
from bot import bot

app = Flask(__name__)

@app.route('/')
def home():
    return "Бот запущен и работает!"

@app.route('/health')
def health():
    return "OK", 200

def run_bot():
    bot.infinity_polling()

if __name__ == "__main__":
    # Запускаем бота в отдельном потоке
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()

    # Запускаем Flask-сервер для Render
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
