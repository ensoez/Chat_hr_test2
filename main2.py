import telebot
from telebot import types
import sqlite3
import os
import sys
import signal
import threading

bot_token = '6989797788:AAHzCllKNdspk3WEhwz7Mt0QuDzhP-NKvb0'
bot = telebot.TeleBot(bot_token)

class UserData:
    def __init__(self):
        self.age = None
        self.full_name = None
        self.has_bicycle = None
        self.city = None
        self.citizenship = None

user_data_dict = {}

# Connect to SQLite database and create couriers table
conn = sqlite3.connect('couriers.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS couriers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                age INTEGER,
                full_name TEXT,
                has_bicycle TEXT,
                city TEXT,
                citizenship TEXT)''')
conn.commit()

# Создаем мьютекс для блокировки доступа к базе данных из разных потоков
db_lock = threading.Lock()

@bot.message_handler(func=lambda message: message.text == 'О вакансии')
def job_vacancy(message):
    bot.send_message(message.chat.id, 'Вакансия курьера "продукты-быстро"\n\nОписание: В этой работе нет штрафов и вообще это лучшая доставка.')


@bot.message_handler(func=lambda message: message.text == 'Рассчитать доход')
def calculate_income(message):
    msg = bot.send_message(message.chat.id, 'Сколько дней в месяц вы хотите работать? (Не более 30)')
    bot.register_next_step_handler(msg, process_days)

def process_days(message):
    try:
        days = int(message.text)
        if days > 30:
            bot.send_message(message.chat.id, 'Количество дней в месяц не может быть больше 30. Пожалуйста, введите заново.')
            bot.register_next_step_handler(message, process_days)
            return
        user_data = UserData()
        user_data.days = days
        user_data_dict[message.chat.id] = user_data

        msg = bot.send_message(message.chat.id, 'Сколько часов в день вы готовы работать? (Не более 16)')
        bot.register_next_step_handler(msg, process_hours)
    except ValueError:
        bot.send_message(message.chat.id, 'Пожалуйста, введите число дней цифрами.')
        bot.register_next_step_handler(message, process_days)

def process_hours(message):
    try:
        hours_per_day = int(message.text)
        if hours_per_day > 16:
            bot.send_message(message.chat.id, 'Количество часов в день не может быть больше 16. Пожалуйста, введите заново.')
            bot.register_next_step_handler(message, process_hours)
            return
        user_data = user_data_dict.get(message.chat.id)
        user_data.hours_per_day = hours_per_day

        hourly_rate = 300  # Assumed hourly rate
        income = user_data.days * user_data.hours_per_day * hourly_rate
        bot.send_message(message.chat.id, f'Ваш заработок за месяц составит {income} рублей')

        markup = types.ReplyKeyboardMarkup(row_width=1)
        itembtn1 = types.KeyboardButton('Подать заявку')
        itembtn2 = types.KeyboardButton('О вакансии')
        itembtn3 = types.KeyboardButton('Рассчитать доход')
        markup.add(itembtn1, itembtn2, itembtn3)

        bot.send_message(message.chat.id, 'Меню', reply_markup=markup)
    except ValueError:
        bot.send_message(message.chat.id, 'Пожалуйста, введите число часов в день цифрами.')
        bot.register_next_step_handler(message, process_hours)

@bot.message_handler(commands=['start', 'main', 'hello'])
def main(message):
    markup = types.ReplyKeyboardMarkup(row_width=1)
    itembtn1 = types.KeyboardButton('Подать заявку')
    itembtn2 = types.KeyboardButton('О вакансии')
    itembtn3 = types.KeyboardButton('Рассчитать доход')
    markup.add(itembtn1, itembtn2, itembtn3)

    bot.send_message(message.chat.id, '<b>Привет</b> <u>я</u> <em>тестовый бот</em>', parse_mode='html', reply_markup=markup)

@bot.message_handler(commands=['help'])
def help_message(message):
    bot.send_message(message.chat.id, 'Help')

@bot.message_handler(func=lambda message: message.text == 'Подать заявку')
def apply_for_job(message):
    msg = bot.send_message(message.chat.id, 'Введите ваше ФИО:')
    bot.register_next_step_handler(msg, process_full_name)

def process_full_name(message):
    user_data = user_data_dict.setdefault(message.chat.id, UserData())
    user_data.full_name = message.text

    msg = bot.send_message(message.chat.id, 'Введите ваш возраст:')
    bot.register_next_step_handler(msg, process_age)

from telebot import types

def process_age(message):
    try:
        age = int(message.text)
        user_data = user_data_dict[message.chat.id]
        user_data.age = age

        markup = types.ReplyKeyboardMarkup(row_width=2)
        itembtn1 = types.KeyboardButton('Да1')
        itembtn2 = types.KeyboardButton('Нет1')
        markup.add(itembtn1, itembtn2)

        msg = bot.send_message(message.chat.id, 'У вас есть велосипед?', reply_markup=markup)
        bot.register_next_step_handler(msg, process_bicycle)
    except ValueError:
        bot.send_message(message.chat.id, 'Пожалуйста, введите возраст цифрами.')
        bot.register_next_step_handler(message, process_age)

def process_bicycle(message):
    user_data = user_data_dict[message.chat.id]
    if message.text == 'Да1':
        user_data.has_bicycle = True
    else:
        user_data.has_bicycle = False

    # Вывод собранных данных для проверки
    bot.send_message(message.chat.id, f'Проверьте введенные данные:\n'
                                      f'ФИО: {user_data.full_name}\n'
                                      f'Возраст: {user_data.age}\n'
                                      f'Наличие велосипеда: {"Да" if user_data.has_bicycle else "Нет"}')

    markup_inline = types.InlineKeyboardMarkup()
    markup_inline.row(
        types.InlineKeyboardButton('Все верно', callback_data='all_correct'),
        types.InlineKeyboardButton('Заполнить заново', callback_data='start_over')
    )

    bot.send_message(message.chat.id, 'Выберите действие:', reply_markup=markup_inline)

    markup_reply = types.ReplyKeyboardMarkup(row_width=1)
    itembtn1 = types.KeyboardButton('Подать заявку')
    itembtn2 = types.KeyboardButton('О вакансии')
    itembtn3 = types.KeyboardButton('Рассчитать доход')
    markup_reply.add(itembtn1, itembtn2, itembtn3)

    bot.send_message(message.chat.id, 'После Подтверждения заявки вы можете рассчитать доход нажав на кнопку ниже:', reply_markup=markup_reply)


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == 'all_correct':
        user_data = user_data_dict[call.message.chat.id]
        save_courier_data(user_data)
        bot.send_message(call.message.chat.id, 'Благодарим за предоставленную информацию! Ваш запрос принят. Менеджер свяжется с вами в ближайшее время.')
        user_data_dict[call.message.chat.id] = UserData()
    elif call.data == 'start_over':
        bot.send_message(call.message.chat.id, 'Начнем заполнение заново.')
        apply_for_job(call.message)

# Функция сохранения данных курьера в базу данных
def save_courier_data(user_data):
    with db_lock:
        cursor.execute("INSERT INTO couriers (age, full_name, has_bicycle, city, citizenship) VALUES (?, ?, ?, ?, ?)",
                       (user_data.age, user_data.full_name, user_data.has_bicycle, user_data.city, user_data.citizenship))
        conn.commit()

def signal_handler(signal, frame):
    print("Выход из программы")
    bot.stop_polling()
    conn.close()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

if __name__ == "__main__":
    bot.polling(none_stop=True)