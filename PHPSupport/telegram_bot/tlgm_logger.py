import logging


class TlgmLogsHandler(logging.Handler):

    def __init__(self, bot, chat_id, formatter):
        super().__init__()
        self.bot = bot
        self.admin_chat_id = chat_id
        self.setFormatter(formatter)

    def emit(self, record):
        self.bot.send_message(
                         chat_id=self.admin_chat_id,
                         text=self.formatter.format(record)
        )
