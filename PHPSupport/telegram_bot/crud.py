from .models import Subcontractor, Client, Request


def is_user_subcontractor(user_id):
    return Subcontractor.objects.filter(telegram_id=user_id).first()


def is_user_client(user_id):
    return Client.objects.filter(telegram_id=user_id).first()


def add_executer(user_id, chat_id, name):
    new_executer = Subcontractor(
        telegram_id=user_id,
        chat_id=chat_id,
        on_check=True,
        status='on_check',
        name=name,
    )
    new_executer.save()


def add_client(user_id):
    pass
    # Fix me  Добавить код добавления клиента по аналогии с исполнителем


def fetch_free_requests():
    free_requests = Request.objects.filter(subcontractor=None)
    if len(free_requests) == 0:
        return None
    return free_requests


def fetch_request(id):
    return Request.objects.get(id=id)
