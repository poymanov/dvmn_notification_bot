import requests
import os
import telegram
import time

DEVMAN_API_URL = os.environ['DEVMAN_API_URL']
DEVMAN_AUTH_TOKEN = os.environ['DEVMAN_AUTH_TOKEN']
TELEGRAM_BOT_TOKEN = os.environ['TELEGRAM_BOT_TOKEN']
TELEGRAM_SOCKS5_PROXY = os.environ['TELEGRAM_SOCKS5_PROXY']
TELEGRAM_USER_CHAT_ID = os.environ['TELEGRAM_USER_CHAT_ID']


def init_telegram_bot():
    proxy_request = None

    if TELEGRAM_SOCKS5_PROXY:
        proxy_request = telegram.utils.request.Request(proxy_url='socks5://{}'.format(TELEGRAM_SOCKS5_PROXY))

    return telegram.Bot(token=TELEGRAM_BOT_TOKEN, request=proxy_request)


def main():
    query_timestamp = None
    need_connection_timeout = False

    bot = init_telegram_bot()

    while True:
        try:
            headers = {'Authorization': 'Token {}'.format(DEVMAN_AUTH_TOKEN)}
            params = {}

            if query_timestamp:
                params['timestamp'] = query_timestamp

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
                bot.send_message(chat_id=TELEGRAM_USER_CHAT_ID, text=message)

                query_timestamp = last_attempt_timestamp
            else:
                query_timestamp = None
        except requests.exceptions.ReadTimeout:
            continue
        except requests.HTTPError:
            message = 'Ошибка подключения к сервису dvmn.org'
            bot.send_message(chat_id=TELEGRAM_USER_CHAT_ID, text=message)
            print(message)
            continue
        except requests.ConnectionError:
            if need_connection_timeout:
                time.sleep(5)
            else:
                need_connection_timeout = True
            continue


if __name__ == '__main__':
    main()
