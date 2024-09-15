Импортируем все необходимые нам библиотеки

from typing import Dict
import telebot
from openpyxl.workbook import Workbook
from telebot import types
from telebot.types import ReplyKeyboardMarkup

Подключаем бота к коду с помощью HTTP API от BotFather

bot = telebot.TeleBot('6988662541:AAF1Mzu3fNr1okYiHUfOxOcUVTfeNwXIihU')  # подключение бота к коду

Создадим обработчик команды /start, которой при ее исполнении будет приветствовать пользователя по имени и спрашивать готов ли он начать

@bot.message_handler(commands=['start'])  # обработчик команды /start
def handler_wellcome(message):  # функция приветствующая гостя
   markup = get_btn_ready()
   bot.send_message(message.chat.id, f'Привет, {message.from_user.first_name}. Вы готовы начать?', reply_markup=markup)
   bot.register_next_step_handler(message, handler_start)

Чтобы пользователю было проще и быстрее отвечать, создаем кнопки “да” и “нет”:

markup = get_btn_ready()  # создание кнопок
Для этого заранее создаем функцию, которая будет отвечать за эти кнопки
def get_btn_ready() -> ReplyKeyboardMarkup:  # функция создающая кнопки да и нет
   markup = types.ReplyKeyboardMarkup()
   btn_yes = types.KeyboardButton('Да')
   btn_no = types.KeyboardButton('Нет')
   markup.row(btn_yes, btn_no)
   return markup

Эта функция создает кнопки и выводит на консоль пол
При ответе пользователя “Да” мы начинаем запрашивать у него необходимые для расчетов данные. Что бы было удобнее собирать и хранить данные, создадим в отдельном файле класс который будет за это отвечать:

from dataclasses import dataclass
@dataclass
class CreditForm:
   duration_month = None
   percent = None
   amount = None
def print(self):
       print(self.duration_month)
       print(self.percent)
       print(self.amount)

После подключаем его к нашему проекту:

from credit_form import CreditForm

Запрашиваем данные пользователя

def handler_start(message):  # функция обрабатывающая ответ на вопрос о готовности
   if message.text == 'Да':
       bot.send_message(message.chat.id, 'Введите срок кредита (в месяцах)', reply_markup=types.ReplyKeyboardRemove())
       bot.register_next_step_handler(message, handle_duration_month)
   elif message.text == 'Нет':
       markup = get_btn_restart()
       bot.send_message(message.chat.id, 'Хорошо, готовы работать с вами в любое время',
                        reply_markup=markup)
       bot.register_next_step_handler(message, handler_wellcome)
def handle_duration_month(message):  # функция обрабатывающая введенный month
   credit_form = get_or_create_credit_form(message.chat.id)
   try:
       credit_form.duration_month = int(message.text)
       bot.send_message(message.chat.id, 'Введите кредитную ставку (процент в год)')
       bot.register_next_step_handler(message, handle_percent)
   except ValueError:
       bot.send_message(message.chat.id, 'Это не число! Попробуйте еще раз')
       bot.register_next_step_handler(message, handle_duration_month)
def handle_percent(message):  # функция обрабатывающая введенный percent
   credit_form = get_or_create_credit_form(message.chat.id)
   try:
       credit_form.percent = float(message.text)
       bot.send_message(message.chat.id, 'Введите сумму кредитования')
       bot.register_next_step_handler(message, handle_amount)
   except ValueError:
       bot.send_message(message.chat.id, 'Это не число! Попробуйте еще раз')
       bot.register_next_step_handler(message, handle_percent)

Каждый раз получая ответ, проверяем является та или иная переменная числом или дробью с помощью конструкции try/except. В случае неправильно ответа, алгоритм будет запрашивать информацию, до тех пор пока не получит информацию определенного типа, после чего будет помещать ее в алфавит, за который отвечает созданный ранее класс
Получив все данные бот спрашивает тип платежа

def handle_amount(message):  # функция обрабатывающая введенный amount
   credit_form = get_or_create_credit_form(message.chat.id)
    try:
       credit_form.amount = float(message.text)
       markup = get_btn_payment_type()
       bot.send_message(message.chat.id, 'Какой вид платежа вы выбрали?', reply_markup=markup)
       bot.register_next_step_handler(message, handle_payment_type)
  except ValueError:
       bot.send_message(message.chat.id, 'Это не число! Попробуйте еще раз')
       bot.register_next_step_handler(message, handle_amount)

Чтобы пользователю было проще ответить, создаем кнопки с видами платежа

def get_btn_payment_type() -> ReplyKeyboardMarkup:  # функция создающая кнопки выбора платежа
   markup = types.ReplyKeyboardMarkup()
   btn_dif = types.KeyboardButton('Дифференцированный платеж')
   markup.row(btn_dif)
   btn_any = types.KeyboardButton('Аннуитетный платеж')
   markup.row(btn_any)
   return markup

И выводим их на консоль

markup = get_btn_payment_type()

При выборе вида платежа, запускается одна из функций расчета по кредиту
Создадим функцию отвечающую за расчет при дифференцированном платеже

def call_differentiated(month, percent, amount):  # функция отвечающая за расчет при дифференцированном платеже
   percent /= 100
   percent /= 12
   remains = amount / month  # ежемесячный платеж по основному долгу
   residual = amount  # остаточная задолженность
   payment_total = 0
   payment_schedule = []
   for i in range(month):
       residual -= remains
       monthly_payment = remains + (residual * percent)  # ежемесячный платеж
       payment_schedule.append(monthly_payment)
       payment_total += monthly_payment  # платеж за весь период
   payment_over = payment_total - amount  # переплата
   return payment_schedule, payment_total, payment_over

Создадим функцию отвечающую за расчет при аннуитетном платеже

def call_annuitant(month, percent, amount):  # функция отвечающая за расчет при аннуитетном платеже
   percent /= 100
   percent /= 12
   k = (percent * ((1 + percent) ** month)) / (((1 + percent) ** month) - 1)  # коэффициент аннуитета
   payment_total = 0
   payment_schedule = []
   for i in range(month):  #
       monthly_payment = k * amount  # ежемесячный платеж
       payment_schedule.append(monthly_payment)
       payment_total += monthly_payment  # платеж за весь период
   payment_over = payment_total - amount  # переплата
   return payment_schedule, payment_total, payment_over

Длина сообщений в телеграмме ограничена, поэтому создаем функцию, которая будет создавать таблицу и помещать туда определенную информацию

def create_file(chat_id: int, payment_schedule: list) -> str:  # функция структурирующая полученные данные
   wb = Workbook()
   ws = wb.active
   ws[f'A1'].value = f'месяц'
   ws[f'B1'].value = f'платёж (руб)'
   for i, payment in enumerate(payment_schedule):
       ws[f'A{i + 2}'].value = i + 1
       ws[f'B{i + 2}'].value = payment
   file_name = f'calc_{chat_id}.xlsx'
   wb.save(file_name)
   return file_name

Создадим функцию которая будет собирать подготавливать сообщение

def send_result(chat_id: int, file_name: str, payment_total, payment_over):  # функция составляющая сообщение
   msg = f'Платеж за весь период составит {payment_total} руб\n'
   msg += f'Переплата будет {payment_over} руб'
   bot.send_message(chat_id, msg)
   bot.send_document(
       chat_id=chat_id,
       caption='ежемесячный платёж',
       document=open(file_name, 'rb'),

Создадим функцию которая будет производить расчет по кредиту, помещать данные о ежемесячном платеже в таблицу и сохранять все в виде готового сообщения

def differentiated(message, month, percent, amount):  # функция для дифференцированного платежа
   payment_schedule, payment_total, payment_over = call_differentiated(month, percent, amount)
   file_name = create_file(message.chat.id, payment_schedule)
   send_result(message.chat.id, file_name, payment_total, payment_over)
def annuitant(message, month, percent, amount):  # функция для аннуитетного платежа
   payment_schedule, payment_total, payment_over = call_annuitant(month, percent, amount)
   file_name = create_file(message.chat.id, payment_schedule)
   send_result(message.chat.id, file_name, payment_total, payment_over)

Отправляем сообщение пользователю

def handle_payment_type(message):  # функция отправляющая сообщение
   credit_form = get_or_create_credit_form(message.chat.id)
   if message.text == 'Дифференцированный платеж':
       differentiated(message, credit_form.duration_month, credit_form.percent, credit_form.amount)
       markup = get_btn_restart()
       bot.send_message(message.chat.id, 'Готовы работать с вами в любое время',
                        reply_markup=markup)
       bot.register_next_step_handler(message, handler_wellcome)
   elif message.text == 'Аннуитетный платеж':
       annuitant(message, credit_form.duration_month, credit_form.percent, credit_form.amount)
       markup = get_btn_restart()
       bot.send_message(message.chat.id, 'Готовы работать с вами в любое время',
                        reply_markup=markup)
       bot.register_next_step_handler(message, handler_wellcome)

Работу бота на этом можно считать законченной, но суть бота в том чтобы всегда можно было воспользоваться его умениями. Для этого создаем функцию отвечающую за создание кнопки “начать с начала”:

def get_btn_restart() -> ReplyKeyboardMarkup:  # функция запускающая бота с начала
   markup = types.ReplyKeyboardMarkup()
   btn_restart = types.KeyboardButton('Начать с начала')
   markup.row(btn_restart)
   return markup

Выводим кнопку на консоль

markup = get_btn_restart()

Теперь при нажатии на эту кнопку бот начнет работать с начала
При ответе пользователя “Нет” на вопрос о готовности начать снова выводим на консоль кнопку “Начать сначала”, при нажатии на которую бот начинает весь цикл сначала
В самом конце кода обязательно прописываем обработчик событий бота

bot.infinity_polling()  # запускает цикл обработки событий бота
