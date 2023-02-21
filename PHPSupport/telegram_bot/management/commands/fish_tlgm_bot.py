import logging
from django.core.management import BaseCommand
from environs import Env
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (CommandHandler, ConversationHandler,
                          CallbackQueryHandler, Filters, MessageHandler,
                          Updater, StringCommandHandler, StringRegexHandler)

from telegram_bot.tlgm_logger import TlgmLogsHandler
from telegram_bot.crud import (is_user_client, is_user_subcontractor,
    add_executer, fetch_free_requests, fetch_request, assign_request,
    fetch_open_user_requests, close_request)

INITIAL_MENU, SPLIT_USERS, HANDLE_AGREEMENT, \
        ACCEPT_AGREEMENT, HANDLE_APPROVE, HANDLE_REQUEST, \
        HANDLE_CHOICE, HANDLE_INWORK_REQUEST, HANDLE_INWORK_CHOICE = (1, 2, 3, 4, 5, 6, 7, 8, 9)

logger = logging.getLogger(__file__)


class Command(BaseCommand):
    def handle(self, *args, **options):
        try:
            main()
        except Exception as exc:
            logger.debug(exc)
            raise


def check_user(update, context):
    if is_user_client(update.message.from_user.id):
        context.bot.send_message(update.message.chat.id, text='Вы клиент!')
        return INITIAL_MENU
    if user := is_user_subcontractor(update.message.from_user.id):
        if user.status == 'enable':
            reply_markup = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton('Свободные заявки', callback_data='getjob'),
                    InlineKeyboardButton('Заявки в работе', callback_data='myjob'),
                ],
            ])
            context.bot.send_message(
                update.message.chat.id,
                text='Исполнитель: XXX',
                reply_markup=reply_markup,
            )
            return HANDLE_APPROVE
        elif user.status == 'on_check':
            context.bot.send_message(update.message.chat.id, text='Ваша заявка на рассмотрении!')
            return ACCEPT_AGREEMENT
        elif user.status == 'disable':
            context.bot.send_message(update.message.chat.id, text='Ваш аккаунт заблокирован')
        else:
            context.bot.send_message(update.message.chat.id, text='Да кто ты такой?')
        return INITIAL_MENU
    reply_markup = InlineKeyboardMarkup(
     [
        [
         InlineKeyboardButton('Я клиент', callback_data='client'),
         InlineKeyboardButton('Я исполнитель', callback_data='executer'),
        ],
     ])
    context.bot.send_message(
        update.message.chat.id,
        text='Добро пожаловать в сервис PHPSupport!'
             'Для продолжения выберите пожалуйста ваш статус',
        reply_markup=reply_markup,
    )
    return SPLIT_USERS


def split_users(update, context):
    query = update.callback_query
    query.answer()
    if query.data == 'executer':
        reply_markup = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton('Да', callback_data='yes'),
                    InlineKeyboardButton('Нет', callback_data='no'),
                ],
            ])
        context.bot.send_message(
            update.callback_query.from_user.id,
            text='Вы согласны с условиями PHPSupport?',
            reply_markup=reply_markup,
        )
        query.delete_message()
        return HANDLE_AGREEMENT
    return INITIAL_MENU


def display_menu():
    pass


def handle_agreement(update, context):
    query = update.callback_query
    query.answer()
    if query.data == 'yes':
        add_executer(
            update.callback_query.from_user.id,
            update.callback_query.message.chat.id,
            update.callback_query.message.chat.username,
        )
        context.bot.send_message(
            update.callback_query.from_user.id,
            text='Заявка отправлена на рассмотрение',
        )
        query.delete_message()
        context.job_queue.run_repeating(check_status, 30, context=query.message.chat.id)
        return ACCEPT_AGREEMENT
    query.delete_message()
    return ConversationHandler.END


def list_requests(update, context):
    query = update.callback_query
    query.answer()
    if requests := fetch_free_requests():
        buttons = []
        for request in requests:
            buttons.append([InlineKeyboardButton(request.title, callback_data=request.id)])
        reply_markup = InlineKeyboardMarkup(buttons)
        context.bot.send_message(query.from_user.id, reply_markup=reply_markup, text='Свободные заявки:')
    else:
        context.bot.send_message(query.from_user.id, text='Список заявок пуст!')
    query.delete_message()
    return HANDLE_REQUEST


def list_requests_callback(update, context):
    query = update.callback_query
    print(query.data)
    query.answer()
    if query.data == 'getjob' or query.data == 'back':
        if requests := fetch_free_requests():
            buttons = []
            for request in requests:
                buttons.append([InlineKeyboardButton(request.title, callback_data=request.id)])
            buttons.append([InlineKeyboardButton("<< Назад", callback_data='back')])
            reply_markup = InlineKeyboardMarkup(buttons)
            context.bot.send_message(query.from_user.id, reply_markup=reply_markup, text='Свободные заявки:')
        else:
            buttons = []
            buttons.append([InlineKeyboardButton("<< Назад", callback_data='back')])
            reply_markup = InlineKeyboardMarkup(buttons)
            context.bot.send_message(query.from_user.id, text='Список заявок пуст!')
        query.delete_message()
        return HANDLE_REQUEST
    if query.data == 'myjob':
        if requests := fetch_open_user_requests(query.from_user.id):
            buttons = []
            for request in requests:
                buttons.append([InlineKeyboardButton(request.title, callback_data=request.id)])
            buttons.append([InlineKeyboardButton("<< Назад", callback_data='back')])
            reply_markup = InlineKeyboardMarkup(buttons)
            context.bot.send_message(query.from_user.id, reply_markup=reply_markup, text='Заявки в работе:')
        else:
            buttons = []
            buttons.append([InlineKeyboardButton("<< Назад", callback_data='back')])
            reply_markup = InlineKeyboardMarkup(buttons)
            context.bot.send_message(query.from_user.id, text='Нет заявок в работе!', reply_markup=reply_markup)
        query.delete_message()
        return HANDLE_INWORK_REQUEST


def display_request(update, context):
    query = update.callback_query
    query.answer()
    if query.data == 'back':
        reply_markup = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton('Свободные заявки', callback_data='getjob'),
                    InlineKeyboardButton('Заявки в работе', callback_data='myjob'),
                ],
            ])
        context.bot.send_message(
                query.from_user.id,
                text='Исполнитель: XXX',
                reply_markup=reply_markup,
            )
        query.delete_message()
        return HANDLE_APPROVE
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton('Взять заказ', callback_data=f'request-{query.data}')],
        [InlineKeyboardButton('<< Назад', callback_data='back')],
    ])
    context.bot.send_message(
        update.callback_query.from_user.id,
        text=fetch_request(query.data).description,
        reply_markup=reply_markup,
    )
    query.delete_message()
    return HANDLE_CHOICE


def cancel(update, _):
    update.message.reply_text('До следующих встреч!')
    return ConversationHandler.END


def handle_choice(update, context):
    query = update.callback_query
    query.answer()
    if query.data == 'back':
        if requests := fetch_free_requests():
            buttons = []
            for request in requests:
                buttons.append([InlineKeyboardButton(request.title, callback_data=request.id)])
            buttons.append([InlineKeyboardButton("<< Назад", callback_data='back')])
            reply_markup = InlineKeyboardMarkup(buttons)
            context.bot.send_message(update.callback_query.from_user.id, reply_markup=reply_markup, text='Список свободных заявок:')
        else:
            buttons = []
            buttons.append([InlineKeyboardButton("<< Назад", callback_data='back')])
            reply_markup = InlineKeyboardMarkup(buttons)
            context.bot.send_message(query.from_user.id, text='Список заявок пуст!')
        query.delete_message()
        return HANDLE_REQUEST
    prefix, request_id = query.data.split('-')
    if prefix == 'request':
        assign_request(update.callback_query.from_user.id, request_id)
        buttons = []
        buttons.append([InlineKeyboardButton("<< Назад", callback_data='back')])
        reply_markup = InlineKeyboardMarkup(buttons)
        context.bot.send_message(update.callback_query.from_user.id, text='Заявка взята в работу', reply_markup=reply_markup)
        query.delete_message()
        return HANDLE_APPROVE
    context.bot.send_message(update.callback_query.from_user.id, text='Все пропало?')


def list_inwork_requests(update, context):
    if requests := fetch_open_user_requests(update.message.from_user.id):
        buttons = []
        for request in requests:
            buttons.append([InlineKeyboardButton(request.title, callback_data=request.id)])
        buttons.append([InlineKeyboardButton("<< Назад", callback_data='back')])
        reply_markup = InlineKeyboardMarkup(buttons)
        context.bot.send_message(update.message.from_user.id, reply_markup=reply_markup, text='Заявки в работе!!!:')
    else:
        buttons = []
        buttons.append([InlineKeyboardButton("<< Назад", callback_data='back')])
        reply_markup = InlineKeyboardMarkup(buttons)
        context.bot.send_message(update.message.from_user.id, text='Нет заявок в работе!', reply_markup=reply_markup)
    return HANDLE_INWORK_REQUEST


def handle_inwork(update, context):
    query = update.callback_query
    query.answer()
    if query.data == 'back':
        reply_markup = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton('Свободные заявки', callback_data='getjob'),
                    InlineKeyboardButton('Заявки в работе', callback_data='myjob'),
                ],
            ])
        context.bot.send_message(
            query.from_user.id,
            text='Исполнитель: XXX',
            reply_markup=reply_markup,
        )
        query.delete_message()
        return HANDLE_APPROVE
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton('Дополнительная информация по заявке', callback_data=f'request-{query.data}')],
        [InlineKeyboardButton('Закрыть заявку', callback_data=f'close-{query.data}')],
        [InlineKeyboardButton('<< Назад', callback_data='back')],
    ])
    context.bot.send_message(
        update.callback_query.from_user.id,
        text=fetch_request(query.data).description,
        reply_markup=reply_markup,
    )
    query.delete_message()
    return HANDLE_INWORK_CHOICE


def handle_inwork_choice(update, context):
    query = update.callback_query
    query.answer()
    if query.data == 'back':
        if requests := fetch_open_user_requests(update.callback_query.from_user.id):
            buttons = []
            for request in requests:
                buttons.append([InlineKeyboardButton(request.title, callback_data=request.id)])
            buttons.append([InlineKeyboardButton("<< Назад", callback_data='back')])
            reply_markup = InlineKeyboardMarkup(buttons)
            context.bot.send_message(update.callback_query.from_user.id, reply_markup=reply_markup, text='Заявки в работе:')
        else:
            context.bot.send_message(update.callback_query.from_user.id, text='Нет заявок в работе!')
        query.delete_message()
        return HANDLE_INWORK_REQUEST
    prefix, request_id = query.data.split('-')
    if prefix == 'close':
        close_request(update.callback_query.from_user.id, request_id)
        context.bot.send_message(update.callback_query.from_user.id, text='Заявка закрыта')
        query.delete_message()
        return HANDLE_APPROVE
    if prefix == 'request':
        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton('<< Назад', callback_data=request_id)],
        ])
        context.bot.send_message(
            update.callback_query.from_user.id,
            text='Здесь будет секретная информация о логинах и паролях',
            reply_markup=reply_markup,
        )
        query.delete_message()
        return HANDLE_INWORK_REQUEST
    context.bot.send_message(update.callback_query.from_user.id, text='Все пропало?')


def error_handler(_, context):
    logger.exception('Exception', exc_info=context.error)


def check_status(context):
    if user := is_user_subcontractor(context.job.context):
        if user.status == 'enable':
            reply_markup = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton('Свободные заявки', callback_data='getjob'),
                    InlineKeyboardButton('Заявки в работе', callback_data='myjob'),
                ],
            ])
            context.bot.send_message(
                context.job.context,
                text='Ваща заявка одобрена!',
                reply_markup=reply_markup,
            )
            context.job.schedule_removal()
            return HANDLE_APPROVE
            

def main():
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )

    env = Env()
    env.read_env()
    tlgm_bot_token = env('TLGM_BOT_TOKEN')

    updater = Updater(tlgm_bot_token)
    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', check_user),
            MessageHandler(Filters.text, check_user),
            ],

        states={
            INITIAL_MENU: [
                        MessageHandler(Filters.text & ~Filters.command,
                                       display_menu),
            ],
            SPLIT_USERS: [CallbackQueryHandler(split_users)],
            HANDLE_AGREEMENT: [
                        CallbackQueryHandler(handle_agreement),
            ],
            ACCEPT_AGREEMENT:  [
                        MessageHandler(Filters.text, check_user),
                        CallbackQueryHandler(list_requests_callback)
            ],
            HANDLE_APPROVE:  [
                        CallbackQueryHandler(list_requests_callback),
                        CommandHandler('list', list_requests),
                        CommandHandler('my', list_inwork_requests),
                        
            ],
            HANDLE_REQUEST:  [
                        CallbackQueryHandler(display_request),
                        CommandHandler('my', list_inwork_requests),
                        CommandHandler('list', list_requests),
            ],
            HANDLE_CHOICE:   [
                        CallbackQueryHandler(handle_choice),
          
            ],
            HANDLE_INWORK_REQUEST: [
                        CallbackQueryHandler(handle_inwork)
            ],
            HANDLE_INWORK_CHOICE:   [
                        CallbackQueryHandler(handle_inwork_choice)
            ]

        },

        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dispatcher.add_handler(conv_handler)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        '%H:%M:%S',
    )
    logger.setLevel(logging.INFO)
    logger.addHandler(TlgmLogsHandler(
        updater.bot,
        env('ADMIN_TLGM_CHAT_ID'),
        formatter
        )
    )
    dispatcher.add_error_handler(error_handler)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
