import requests
import os
import telegram
import time
import logging

DEVMAN_API_URL = os.environ['DEVMAN_API_URL']
DEVMAN_AUTH_TOKEN = os.environ['DEVMAN_AUTH_TOKEN']
TELEGRAM_NOTIFICATION_BOT_TOKEN = os.environ['TELEGRAM_NOTIFICATION_BOT_TOKEN']
TELEGRAM_ADMIN_BOT_TOKEN = os.environ['TELEGRAM_ADMIN_BOT_TOKEN']
TELEGRAM_SOCKS5_PROXY = os.environ['TELEGRAM_SOCKS5_PROXY']
TELEGRAM_USER_CHAT_ID = os.environ['TELEGRAM_USER_CHAT_ID']


logger = logging.getLogger(__file__)


class TelegramLogsHandler(logging.Handler):
    def __init__(self, tg_bot, chat_id):
        super().__init__()
        self.chat_id = chat_id
        self.tg_bot = tg_bot

    def emit(self, record):
        log_entry = self.format(record)
        self.tg_bot.send_message(chat_id=self.chat_id, text=log_entry)


def init_telegram_bot(token):
    proxy_request = None

    if TELEGRAM_SOCKS5_PROXY:
        proxy_request = telegram.utils.request.Request(proxy_url='socks5://{}'.format(TELEGRAM_SOCKS5_PROXY))

    return telegram.Bot(token=token, request=proxy_request)


def main():
    query_timestamp = None

    notification_bot = init_telegram_bot(TELEGRAM_NOTIFICATION_BOT_TOKEN)

    logger.warning('Бот запущен')

    while True:
        try:
            headers = {'Authorization': 'Token {}'.format(DEVMAN_AUTH_TOKEN)}
            params = {'timestamp': query_timestamp}

            response = requests.get(DEVMAN_API_URL, headers=headers, params=params, timeout=90)
            response.raise_for_status()

            response_data = response.json()

            response_data_status = response_data['status']

            if response_data_status == 'timeout':
                query_timestamp = response_data['timestamp_to_request']
            elif response_data_status == 'found':
                attempt_data = response_data['new_attempts'][0]
                lesson_title = attempt_data['lesson_title']
                lesson_negative = attempt_data['is_negative']
                last_attempt_timestamp = response_data['last_attempt_timestamp']

                if lesson_negative:
                    lesson_result_message = 'К сожалению, в работе нашлись ошибки.'
                else:
                    lesson_result_message = 'Преподавателю всё понравилось, можно приступать к следующему уроку!'

                message = 'У вас проверили работу "{}".\n\n{}'.format(lesson_title, lesson_result_message)
                notification_bot.send_message(chat_id=TELEGRAM_USER_CHAT_ID, text=message)

                query_timestamp = last_attempt_timestamp
            else:
                query_timestamp = None
        except (requests.exceptions.ReadTimeout, requests.ConnectionError):
            continue
        except requests.HTTPError:
            message = 'Ошибка подключения к сервису dvmn.org'
            notification_bot.send_message(chat_id=TELEGRAM_USER_CHAT_ID, text=message)
            logger.warning(message)
            continue
        except Exception:
            logger.exception('Бот упал с ошибкой')


if __name__ == '__main__':
    admin_bot = init_telegram_bot(TELEGRAM_ADMIN_BOT_TOKEN)

    logger.setLevel(logging.WARNING)
    logger.addHandler(TelegramLogsHandler(admin_bot, TELEGRAM_USER_CHAT_ID))

    main()
