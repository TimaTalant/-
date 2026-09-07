import telebot
import os
import re
from supabase import create_client
from dotenv import load_dotenv
from telebot import types
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler

# ==================== ЗАГРУЗКА ТОКЕНА И ADMIN_ID ====================
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

if not BOT_TOKEN:
    raise RuntimeError("Токен не найден в файле .env")

bot = telebot.TeleBot(BOT_TOKEN)


# ==================== ГЛОБАЛЬНАЯ ПЕРЕМЕННАЯ ====================
active_bookings = set()

# ==================== ГЛАВНОЕ МЕНЮ ====================
def main_menu():
    keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton('📋 Услуги')
    btn2 = types.KeyboardButton('📅 Записаться')
    btn3 = types.KeyboardButton('📍 Контакты')
    btn4 = types.KeyboardButton('❓ Вопрос')
    btn5 = types.KeyboardButton('📝 Отзывы')
    btn6 = types.KeyboardButton('💼 Кейсы')
    keyboard.add(btn1, btn2, btn3, btn4, btn5, btn6)
    return keyboard

# ==================== КЛАВИАТУРА С ОТМЕНОЙ ====================
def cancel_keyboard():
    keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    btn = types.KeyboardButton('❌ Отмена')
    keyboard.add(btn)
    return keyboard

# ==================== КОМАНДА /start ====================
@bot.message_handler(commands=['start'])
def start(message):
    active_bookings.discard(message.chat.id)
    bot.send_message(
        message.chat.id,
        f"Привет! {message.from_user.first_name} ✨\nДобро пожаловать. Выберите действие:",
        reply_markup=main_menu()
    )

# ==================== КОМАНДА /cancel ====================
@bot.message_handler(commands=['cancel'])
def cancel(message):
    active_bookings.discard(message.chat.id)
    bot.send_message(
        message.chat.id,
        "❌ Запись отменена. Вы можете начать заново.",
        reply_markup=main_menu()
    )

# ==================== ОБРАБОТЧИК КОМАНД ====================
@bot.message_handler(commands=['price'])
def price_command(message):
    bot.send_message(message.chat.id, "Услуги:")

@bot.message_handler(commands=['contact'])
def contacts_command(message):
    bot.send_message(message.chat.id, "📍 Адрес:***** \n📞 Телефон: +7 (999) 123-45-67\n📸 Instagram: @*******")

@bot.message_handler(commands=['reservation'])
def reservation_command(message):
    active_bookings.add(message.chat.id)
    msg = bot.send_message(
        message.chat.id,
        "Введите ваше имя:\n\n(Чтобы отменить запись, напишите /cancel)",
        reply_markup=cancel_keyboard()
    )
    bot.register_next_step_handler(msg, get_phone)

@bot.message_handler(commands=['quest'])
def quest_command(message):
    msg = bot.send_message(
        message.chat.id,
        "📝 Напишите ваш вопрос.\n\n(Чтобы отменить, напишите /cancel)",
        reply_markup=cancel_keyboard()
    )
    bot.register_next_step_handler(msg, handle_quest)

# ==================== ОБРАБОТЧИК КНОПОК ====================
@bot.message_handler(func=lambda message: True)
def handle_buttons(message):
    if message.chat.id in active_bookings:
        return

    if message.text == '📋 Услуги':
        bot.send_message(message.chat.id, "Услуги: ")
    elif message.text == '📍 Контакты':
        bot.send_message(message.chat.id, "📍 Адрес:***** \n📞 Телефон: +7 (999) 123-45-67\n📸 Instagram: @*******")
    elif message.text == '📝 Отзывы':
        bot.send_message(message.chat.id, "📝 Чат с отзывами: https://t.me/.")
    elif message.text == '💼 Кейсы':
        bot.send_message(message.chat.id, "💼 Кейсы: https://t.me/.")
    elif message.text == '❓ Вопрос':
        msg = bot.send_message(
            message.chat.id,
            "📝 Напишите ваш вопрос.\n\n(Чтобы отменить, напишите /cancel)",
            reply_markup=cancel_keyboard()
        )
        bot.register_next_step_handler(msg, handle_quest)
    elif message.text == '📅 Записаться':
        active_bookings.add(message.chat.id)
        msg = bot.send_message(
            message.chat.id,
            "Введите ваше имя:\n\n(Чтобы отменить запись, напишите /cancel)",
            reply_markup=cancel_keyboard()
        )
        bot.register_next_step_handler(msg, get_phone)
    elif message.text == '❌ Отмена':
        cancel(message)

# ==================== РЕГИСТРАЦИЯ ====================
def get_phone(message):
    if message.text == '/cancel' or message.text == '❌ Отмена':
        cancel(message)
        return
    name = message.text
    if not name.strip():
        msg = bot.send_message(message.chat.id, "❌ Имя не может быть пустым. Введите имя:", reply_markup=cancel_keyboard())
        bot.register_next_step_handler(msg, get_phone)
        return
    msg = bot.send_message(message.chat.id, "Введите ваш номер телефона:", reply_markup=cancel_keyboard())
    bot.register_next_step_handler(msg, get_service, name)

def get_service(message, name):
    if message.text == '/cancel' or message.text == '❌ Отмена':
        cancel(message)
        return
    phone = message.text
    phone_clean = re.sub(r'[\s\-\(\)]', '', phone)
    if not re.match(r'^\+?\d{10,15}$', phone_clean):
        msg = bot.send_message(message.chat.id, "❌ Неверный формат телефона. Введите номер:", reply_markup=cancel_keyboard())
        bot.register_next_step_handler(msg, get_service, name)
        return
    msg = bot.send_message(message.chat.id, "Введите услугу:", reply_markup=cancel_keyboard())
    bot.register_next_step_handler(msg, get_date, name, phone)

def get_date(message, name, phone):
    if message.text == '/cancel' or message.text == '❌ Отмена':
        cancel(message)
        return
    service = message.text
    if not service.strip():
        msg = bot.send_message(message.chat.id, "❌ Услуга не может быть пустой. Введите услугу:", reply_markup=cancel_keyboard())
        bot.register_next_step_handler(msg, get_date, name, phone)
        return
    msg = bot.send_message(message.chat.id, "Введите дату (например, 01.09 или 2026-09-01):", reply_markup=cancel_keyboard())
    bot.register_next_step_handler(msg, validate_date, name, phone, service)

def validate_date(message, name, phone, service):
    if message.text == '/cancel' or message.text == '❌ Отмена':
        cancel(message)
        return
    date = message.text
    if not re.match(r'^\d{2}\.\d{2}$|^\d{4}-\d{2}-\d{2}$', date):
        msg = bot.send_message(message.chat.id, "❌ Неверный формат даты. Введите ДД.ММ или ГГГГ-ММ-ДД:", reply_markup=cancel_keyboard())
        bot.register_next_step_handler(msg, validate_date, name, phone, service)
        return
    try:
        if '.' in date:
            day, month = date.split('.')
            datetime(2000, int(month), int(day))
        else:
            year, month, day = date.split('-')
            datetime(int(year), int(month), int(day))
    except ValueError:
        msg = bot.send_message(message.chat.id, "❌ Такой даты не существует. Проверьте ввод:", reply_markup=cancel_keyboard())
        bot.register_next_step_handler(msg, validate_date, name, phone, service)
        return
    msg = bot.send_message(message.chat.id, "Введите время (например, 15:00):", reply_markup=cancel_keyboard())
    bot.register_next_step_handler(msg, validate_time, name, phone, service, date)

def validate_time(message, name, phone, service, date):
    if message.text == '/cancel' or message.text == '❌ Отмена':
        cancel(message)
        return
    time = message.text
    if not re.match(r'^\d{2}:\d{2}$', time):
        msg = bot.send_message(message.chat.id, "❌ Неверный формат времени. Введите ЧЧ:ММ:", reply_markup=cancel_keyboard())
        bot.register_next_step_handler(msg, validate_time, name, phone, service, date)
        return
    hours, minutes = time.split(':')
    if not (0 <= int(hours) <= 23 and 0 <= int(minutes) <= 59):
        msg = bot.send_message(message.chat.id, "❌ Неверное время. Введите часы 0-23 и минуты 0-59:", reply_markup=cancel_keyboard())
        bot.register_next_step_handler(msg, validate_time, name, phone, service, date)
        return
    save_booking(message, name, phone, service, date, time)

def save_booking(message, name, phone, service, date, time):
    active_bookings.discard(message.chat.id)
    datetime_str = f"{date} {time}"

    data = {
        "user_id": message.chat.id,
        "name": name,
        "phone": phone,
        "service": service,
        "date": date,
        "time": time
    }
    supabase.table('bookings').insert(data).execute()

    bot.send_message(
        message.chat.id,
        f"✅ Вы записаны на {datetime_str}!\nМы напомним вам за день 😊",
        reply_markup=main_menu()
    )

# ==================== ОБРАБОТКА ВОПРОСОВ ====================
def handle_quest(message):
    if message.text == '/cancel' or message.text == '❌ Отмена':
        cancel(message)
        return
    user_question = message.text
    user_name = message.from_user.first_name
    username = message.from_user.username or "нет username"
    bot.send_message(ADMIN_ID, f"📩 Новый вопрос от {user_name} (@{username}):\n\n{user_question}")
    bot.send_message(message.chat.id, "✅ Ваш вопрос отправлен. Мы свяжемся с вами.", reply_markup=main_menu())

# ==================== ПРОСМОТР ЗАПИСЕЙ ====================
@bot.message_handler(commands=['bookings'])
def bookings_command(message):
    if message.chat.id != ADMIN_ID:
        bot.send_message(message.chat.id, "⛔ Нет доступа.")
        return

    response = supabase.table('bookings').select('*').order('id', desc=True).limit(20).execute()
    rows = response.data

    if not rows:
        bot.send_message(message.chat.id, "📭 Записей пока нет.")
        return

    text = "📋 **Последние записи:**\n\n"
    for row in rows:
        text += f"#{row['id']} | {row['name']} | {row['phone']}\n   {row['service']} | {row['date']} {row['time']}\n\n"
    bot.send_message(message.chat.id, text, parse_mode='Markdown')  

# ==================== НАПОМИНАНИЯ ====================
def send_reminders():
    tomorrow = datetime.now() + timedelta(days=1)
    tomorrow_str = tomorrow.strftime("%Y-%m-%d")

    response = supabase.table('bookings').select('user_id, name, time, service').eq('date', tomorrow_str).execute()
    bookings = response.data

    for b in bookings:
        try:
            bot.send_message(
                b['user_id'],
                f"🔔 Напоминаем о записи на завтра!\n\n👤 {b['name']}\n💇 {b['service']}\n⏰ {b['time']}\n\nЕсли не сможете прийти — отмените запись."
            )
        except Exception as e:
            print(f"Ошибка отправки {b['user_id']}: {e}")


# ==================== ЗАПУСК ====================
if __name__ == "__main__":
    scheduler = BackgroundScheduler()
    scheduler.add_job(send_reminders, 'cron', hour=10, minute=0)
    scheduler.start()
    print("Бот запущен...")
    bot.infinity_polling()
