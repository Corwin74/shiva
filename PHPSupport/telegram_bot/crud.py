from .models import Subcontractor, Client


def is_user_subcontractor(user_id):
    return Subcontractor.objects.filter(telegram_id=user_id).first()


def is_user_client(user_id):
    return Client.objects.filter(telegram_id=user_id).first()


def add_executer(user_id, chat_id):
    new_executer = Subcontractor(
        telegram_id=user_id,
        chat_id=chat_id,
        on_check=True,
        name='Пока одинаковое'
    )
    new_executer.save()


def add_client(user_id):
    pass
    # Fix me  Добавить код добавления клиента по аналогии с исполнителем
