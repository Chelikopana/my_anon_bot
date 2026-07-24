import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8641022610:AAF6TPxGbvZsZyJfipvh9p8xnSkVyoO6Vho"
bot = telebot.TeleBot(TOKEN)

SECRET_QUESTION = "Кто такой ЧБЧГ?"
SECRET_ANSWERS = [
    "чёрно-белый чонгук",
    "черно-белый чонгук",
    "чёрно белый чонгук",
    "черно белый чонгук"
]

verified_users = []
user_gender = {}
user_preference = {}
chats = {}

def gender_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    b1 = InlineKeyboardButton("Мужской", callback_data="gender_male")
    b2 = InlineKeyboardButton("Женский", callback_data="gender_female")
    keyboard.add(b1, b2)
    return keyboard

def preference_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=3)
    b1 = InlineKeyboardButton("Мужской", callback_data="pref_male")
    b2 = InlineKeyboardButton("Женский", callback_data="pref_female")
    b3 = InlineKeyboardButton("Неважно", callback_data="pref_any")
    keyboard.add(b1, b2, b3)
    return keyboard

@bot.message_handler(commands=['start'])
def start(message):
    uid = message.chat.id
    if uid in verified_users:
        bot.send_message(uid, "Вы уже авторизованы. Используйте /find")
        return
    bot.send_message(uid, f"Добро пожаловать!\n\nОтветьте на вопрос: {SECRET_QUESTION}")

@bot.message_handler(commands=['find'])
def find(message):
    uid = message.chat.id
    if uid not in verified_users:
        bot.send_message(uid, "Сначала ответьте на вопрос /start")
        return
    if uid in chats and chats[uid]:
        bot.send_message(uid, "Вы уже в чате. Используйте /next")
        return
    if uid not in user_gender:
        bot.send_message(uid, "Укажите ваш пол:", reply_markup=gender_keyboard())
        return
    if uid not in user_preference:
        bot.send_message(uid, "Кого ищете?", reply_markup=preference_keyboard())
        return
    find_partner(uid)

@bot.message_handler(commands=['next'])
def next_partner(message):
    uid = message.chat.id
    if uid not in verified_users:
        bot.send_message(uid, "Сначала авторизуйтесь")
        return
    if uid in chats and chats[uid]:
        partner = chats[uid]
        chats[uid] = None
        if partner in chats:
            chats[partner] = None
        bot.send_message(uid, "Завершили чат. Ищем нового...")
        bot.send_message(partner, "Собеседник завершил чат.")
    find_partner(uid)

@bot.message_handler(commands=['stop'])
def stop(message):
    uid = message.chat.id
    if uid in chats and chats[uid]:
        partner = chats[uid]
        chats[uid] = None
        if partner in chats:
            chats[partner] = None
        bot.send_message(uid, "Вы вышли из чата.")
        bot.send_message(partner, "Собеседник вышел из чата.")
    else:
        bot.send_message(uid, "Вы не в чате.")

@bot.message_handler(commands=['settings'])
def settings(message):
    uid = message.chat.id
    if uid not in verified_users:
        bot.send_message(uid, "Сначала авторизуйтесь")
        return
    bot.send_message(uid, "Настройки:", reply_markup=gender_keyboard())

def find_partner(uid):
    preference = user_preference[uid]
    my_gender = user_gender[uid]
    for other in chats:
        if other == uid:
            continue
        if chats[other] is not None:
            continue
        if other not in verified_users:
            continue
        op = user_preference.get(other)
        og = user_gender.get(other)
        if not op or not og:
            continue
        if preference != "any" and og != preference:
            continue
        if op != "any" and my_gender != op:
            continue
        chats[other] = uid
        chats[uid] = other
        bot.send_message(other, "✅ Собеседник найден! Пишите анонимно.\n\n📌 Команды:\n/stop — выйти из чата\n/next — найти нового собеседника")
        bot.send_message(uid, "✅ Собеседник найден! Пишите анонимно.\n\n📌 Команды:\n/stop — выйти из чата\n/next — найти нового собеседника")
        return
    chats[uid] = None
    bot.send_message(uid, "😔 Собеседник не найден. Попробуйте /settings")

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    uid = call.message.chat.id
    if call.data.startswith("gender_"):
        gender = call.data.split("_")[1]
        user_gender[uid] = gender
        bot.edit_message_text("Пол сохранен. Теперь выберите кого ищете:", uid, call.message.message_id, reply_markup=preference_keyboard())
        return
    if call.data.startswith("pref_"):
        pref = call.data.split("_")[1]
        user_preference[uid] = pref
        bot.edit_message_text("Настройки сохранены. Ищем...", uid, call.message.message_id)
        find_partner(uid)
        return

@bot.message_handler(func=lambda msg: True)
def handle_messages(message):
    uid = message.chat.id
    text = message.text.lower().strip()
    if uid not in verified_users:
        if text in [ans.lower() for ans in SECRET_ANSWERS]:
            verified_users.append(uid)
            bot.send_message(uid, "Верно! Теперь укажите ваш пол:", reply_markup=gender_keyboard())
        else:
            bot.send_message(uid, f"Неверно. Попробуйте еще раз: {SECRET_QUESTION}")
        return
    if uid in chats and chats[uid]:
        bot.send_message(chats[uid], message.text)
    else:
        bot.send_message(uid, "Вы не в чате. Нажмите /find")

import threading
import time

# Запускаем бота в отдельном потоке (чтобы он не блокировал веб-сервер)
def run_bot():
    bot.polling(none_stop=True)

thread = threading.Thread(target=run_bot)
thread.start()

# Запускаем простой веб-сервер, чтобы Render видел, что приложение живо
from flask import Flask
app = Flask(__name__)

@app.route('/')
def home():
    return "Бот работает!"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)