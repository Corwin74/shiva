import logging
from django.core.management import BaseCommand
from environs import Env
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (CommandHandler, ConversationHandler,
                          CallbackQueryHandler, Filters, MessageHandler,
                          Updater)

from telegram_bot.tlgm_logger import TlgmLogsHandler
from telegram_bot.crud import (is_user_client, is_user_subcontractor,
    add_executer, fetch_free_requests, fetch_request)

INITIAL_MENU, SPLIT_USERS, HANDLE_AGREEMENT, \
        ACCEPT_AGREEMENT, WAITING_EMAIL = (1, 2, 3, 4, 5)

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
            context.bot.send_message(update.message.chat.id, text='Вы контрактор!')
        elif user.status == 'on_check':
            context.bot.send_message(update.message.chat.id, text='Ваша заявка на рассмотрении!')
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
    print('handle argeemenrt')
    query = update.callback_query
    query.answer()
    if query.data == 'yes':
        return ACCEPT_AGREEMENT
    return INITIAL_MENU


def list_requests(update, context):
    if requests := fetch_free_requests():
        buttons = []
        for request in requests:
            buttons.append(InlineKeyboardButton(request.title, callback_data=request.id))
        reply_markup = InlineKeyboardMarkup([buttons])
        context.bot.send_message(update.message.from_user.id, reply_markup=reply_markup, text='Список свободных заявок:')
    else:
        context.bot.send_message(update.message.from_user.id, text='Список заявок пуст!')
    return ACCEPT_AGREEMENT


def cancel(update, _):
    update.message.reply_text('До следующих встреч!')
    return ConversationHandler.END


def handle_cart(update, context):
    query = update.callback_query
    query.answer()
    client_id = query['from_user']['id']
    if query['data'] == 'email':
        context.bot.send_message(
            client_id,
            'Для оформления заказа укажите адрес электронной почты:',
        )
        return WAITING_EMAIL
    if not query['data'] == 'cart':
        _, item_id = query['data'].split('_')
        remove_product_from_cart(
            context,
            client_id,
            item_id
        )
    menu_buttons = []
    message_text = ""
    for item in get_cart_items(context, client_id):
        menu_buttons.append(
            [
                InlineKeyboardButton(
                    f'{item["name"]} - удалить из корзины',
                    callback_data=f'delete_{item["id"]}',
                )
            ]
        )
        display_price = item["meta"]["display_price"]["with_tax"]
        message_text += f'{item["name"]}\n'\
            f'{display_price["unit"]["formatted"]} за кг.\n'\
            f'В корзине {item["quantity"]} кг.'\
            f'на сумму: {display_price["value"]["formatted"]}\n\n'
    menu_buttons.append(
        [InlineKeyboardButton('В меню', callback_data='back')]
    )
    if message_text:
        cart_cost = get_cart_cost(context, client_id)
        message_text += f'Общая сумма заказа: {cart_cost}\n'
        menu_buttons.append(
            [InlineKeyboardButton('Оформить заказ', callback_data='email')]
        )
    else:
        message_text = "Корзина пуста"
    reply_markup = InlineKeyboardMarkup(menu_buttons)
    context.bot.send_message(
        client_id,
        message_text,
        reply_markup=reply_markup,
    )
    query.delete_message()
    return ACCEPT_AGREEMENT


def handle_email(update, context):
    message = update.message.to_dict()
    response = create_customer(
        context,
        message['text'],
        message['from']['username'],
    )
    email = get_customer(context, response['id'])['email']
    update.message.reply_text(
        f'Спасибо за заказ! Вы указали электронный адрес: {email}'
    )
    return ConversationHandler.END


def wrong_email(update, _):
    update.message.reply_text(
        'Неправильный формат email адреса. Попробуйте еще раз')
    return WAITING_EMAIL


def error_handler(_, context):
    logger.exception('Exception', exc_info=context.error)


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
        entry_points=[CommandHandler('start', check_user)],

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
                        CommandHandler('list', list_requests),
                        CallbackQueryHandler(handle_cart),
                          ],
            WAITING_EMAIL:  [
                        MessageHandler(Filters.entity('email'), handle_email),
                        MessageHandler(Filters.text & ~Filters.command,
                                       wrong_email),
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
