import logging
from django.core.management import BaseCommand
import telebot
from environs import Env
from telebot import types
from telebot.storage import StateMemoryStorage
from telebot import custom_filters
from telebot.handler_backends import State, StatesGroup

from telegram_bot.crud import (is_user_client, is_user_subcontractor,
    add_executer, fetch_free_requests, fetch_request)


logger = logging.getLogger(__file__)


class Command(BaseCommand):
    def handle(self, *args, **options):
        try:
            start_bot()
        except Exception as exc:
            logger.debug(exc)
            raise


def start_bot():

    env = Env()
    env.read_env()
    tlgm_bot_token = env('TLGM_BOT_TOKEN')
    bot = telebot.TeleBot(tlgm_bot_token)
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    #bot_command = types.BotCommand('start', 'start page', 'list')
    #bot.set_my_commands([bot_command])

    @bot.message_handler(commands=['start'])
    def check_user(message):
        if is_user_client(message.from_user.id):
            bot.send_message(message.chat.id, text='Вы клиент!')
            return
        if user := is_user_subcontractor(message.from_user.id):
            if user.status == 'enable':
                bot.send_message(message.chat.id, text='Вы контрактор!')
            elif user.status == 'on_check':
                bot.send_message(message.chat.id, text='Ваша заявка на рассмотрении!')
            elif user.status == 'disable':
                bot.send_message(message.chat.id, text='Ваш аккаунт заблокироан')
            else:
                bot.send_message(message.chat.id, text='Да кто ты такой?')
            return
        button1 = types.InlineKeyboardButton(
            'Я-клиент',
            callback_data='client',
        )
        button2 = types.InlineKeyboardButton(
            'Я-подрядчик',
            callback_data='executer',
        )
        markup = types.InlineKeyboardMarkup()
        markup.add(button1, button2)
        bot.send_message(
            message.chat.id,
            reply_markup=markup,
            text='Добро пожаловать в сервис PHPSupport! Для продолжения выберите'
                 'пожалуйста ваш статус'
        )

    @bot.callback_query_handler(func=lambda call: call.data == "client")
    def client(call: types.CallbackQuery):
        bot.answer_callback_query(callback_query_id=call.id)
        bot.send_message(call.message.chat.id, text="Зарегистрировать вас как клиента?")

    @bot.callback_query_handler(func=lambda call: call.data == "executer")
    def executer(call: types.CallbackQuery):
        bot.answer_callback_query(callback_query_id=call.id)
        button1 = types.InlineKeyboardButton('Да', callback_data='yes_executer')
        button2 = types.InlineKeyboardButton('Нет', callback_data='no_executer')
        markup = types.InlineKeyboardMarkup()
        markup.add(button1, button2)
        bot.send_message(
            call.message.chat.id,
            reply_markup=markup,
            text='Вы согласны с условиями PHPSupport?'
        )

    @bot.callback_query_handler(func=lambda call: call.data == "yes_executer")
    def yes_executer(call: types.CallbackQuery):
        bot.answer_callback_query(callback_query_id=call.id)
        add_executer(call.from_user.id, call.message.chat.id, call.from_user.username)
        bot.send_message(call.message.chat.id, text="Заявка отправлена на рассмотрение")

    @bot.message_handler(commands=['list'])
    def list_requests(message):
        if requests := fetch_free_requests():
            buttons = []
            markup = types.InlineKeyboardMarkup()
            for request in requests:
                markup.add(types.InlineKeyboardButton(request.title, callback_data=request.id))
            bot.send_message(message.chat.id, reply_markup=markup, text='Список свободных заявок:')
        else:
            bot.send_message(message.chat.id, text='Список заявок пуст!')

    @bot.callback_query_handler(func=lambda call: True)
    def display_request(call: types.CallbackQuery):
        bot.answer_callback_query(callback_query_id=call.id)
        bot.send_message(call.message.chat.id, text=fetch_request(call.data).description)

    bot.infinity_polling()
