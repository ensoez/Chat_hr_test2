import telebot
import sqlite3
import os
import sys
import signal
from telebot import types

bot_token = '7052764412:AAEVsiLzso_J_4t_vmJrPKlAeQIAuGHxysk'
bot = telebot.TeleBot(bot_token)

new_applications_count = 0

# Функция для отображения заявок из базы данных
def show_applications(message):
    global new_applications_count
    conn = sqlite3.connect('couriers.db')
    cursor = conn.cursor()

    # Получаем заявки из базы данных
    cursor.execute("SELECT * FROM couriers WHERE viewed = 0")
    new_applications = cursor.fetchall()

    if new_applications:
        for application in new_applications:
            bot.send_message(message.chat.id, f"Новая заявка #{application[0]}:\nВозраст: {application[1]}\nФИО: {application[2]}\nВелосипед: {application[3]}\nГород: {application[4]}\nГражданство: {application[5]}")
            new_applications_count += 1
            cursor.execute("UPDATE couriers SET viewed = 1 WHERE id = ?", (application[0],))

    if new_applications_count > 0:
        bot.send_message(message.chat.id, f"Всего новых заявок: {new_applications_count}")
    else:
        bot.send_message(message.chat.id, "Новых заявок нет.")

    conn.close()

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup()
    btn_show_applications = types.InlineKeyboardButton(text='Посмотреть заявки', callback_data='show_applications')
    btn_show_new_applications = types.InlineKeyboardButton(text='Новые заявки', callback_data='show_new_applications')
    markup.add(btn_show_applications, btn_show_new_applications)

    bot.send_message(message.chat.id, 'Привет! Я бот для просмотра заявок.', reply_markup=markup)

# Обработчик нажатия на инлайн кнопку "Посмотреть заявки"
@bot.callback_query_handler(func=lambda call: call.data == 'show_applications')
def callback_show_applications(call):
    show_applications(call.message)

# Обработчик нажатия на инлайн кнопку "Новые заявки"
@bot.callback_query_handler(func=lambda call: call.data == 'show_new_applications')
def callback_show_new_applications(call):
    global new_applications_count
    show_applications(call.message)
    new_applications_count = 0  # Обнуляем счетчик после просмотра новых заявок

# Обработчик сигнала завершения программы
def signal_handler(signal, frame):
    print("Выход из программы")
    bot.stop_polling()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# Основной цикл программы
if __name__ == "__main__":
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            print(f"Ошибка: {e}")
            bot.stop_polling()
            print("Перезапуск через 3 секунды...")
            os.system("ping 127.0.0.1 -n 4 > nul")  # Ждем 3 секунды перед перезапуском
