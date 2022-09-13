import logging
import os
import requests
import sys
import time

from http import HTTPStatus
from dotenv import load_dotenv
import telegram

from exceptions import BadStatusResponse

main_logger = logging.getLogger(__name__)
main_logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter(
    '%(asctime)s %(levelname)s %(message)s'
)
handler.setFormatter(formatter)
main_logger.addHandler(handler)

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """Отправка сообщения в Телеграм о статусе проверки дом.задания."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        main_logger.info(f'Отправка сообщения в Телеграм чат с ID '
                         f'{TELEGRAM_CHAT_ID}, с текстом "{message}".')
    except Exception as error:
        main_logger.error('Не удалось отправить сообщение в Телеграм чат'
                          f' с ID {TELEGRAM_CHAT_ID}. Ошибка: "{error}".')


def get_api_answer(current_timestamp):
    """Получение json по запросу из API сервиса Практикум.Домашка."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    headers = {'Authorization': 'OAuth ' + PRACTICUM_TOKEN}

    try:
        response = requests.get(ENDPOINT, headers=headers, params=params)
        if response.status_code != HTTPStatus.OK:
            raise BadStatusResponse(
                f'Эндпоинт {ENDPOINT} недоступен. '
                f'Код ответа сервера: {response.status_code}'
            )
    except BadStatusResponse as error:
        raise error
    else:
        main_logger.debug(
            'Получен ответ от API сервиса Практикум.Домашка. '
            f'Код ответа сервера: {response.status_code}'
        )
        return response.json()


def check_response(response):
    """Проверка ответа сервиса на корректность типов."""
    try:
        response_keys = {'homeworks': list, 'current_date': int}
        if not isinstance(response, dict):
            raise TypeError('Тип значения response не является dict')
        else:
            for key, val in response_keys.items():
                if key not in response:
                    raise KeyError(
                        f'Отсутствуют обязательный ключ {key} '
                        'в ответе API сервиса Практикум.Домашка'
                    )
                if not isinstance(response[key], val):
                    raise TypeError(
                        f'Тип значения {key} не является {val.__name__}'
                    )
    except KeyError as error:
        raise error
    except TypeError as error:
        raise error
    else:
        main_logger.debug('Проверка response прошла успешно.')
        return response.get('homeworks')


def parse_status(homework):
    """Парсинг сообщения о статусе проверки домашней работы."""
    try:
        parse_keys = ('status', 'homework_name')
        for parse_key in parse_keys:
            if parse_key not in homework:
                raise KeyError(
                    f'При парсинге домашней работы не '
                    f'обнаружен ключ "{parse_key}"'
                )
        homework_status = homework['status']
        homework_name = homework['homework_name']
        if homework_status not in HOMEWORK_STATUSES:
            raise KeyError(
                'Недокументированный статус домашней '
                f'работы "{homework_status}"'
            )
        verdict = HOMEWORK_STATUSES[homework_status]
    except KeyError as error:
        raise error
    else:
        main_logger.debug('Парсинг прошёл успешно.')
        message = (
            f'Изменился статус проверки работы "{homework_name}". '
            f'{verdict}'
        )
        main_logger.info(message)
        return message


def check_tokens():
    """Функция проверки наличия обязательных переменных."""
    tokens = {
        'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
        'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
        'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID
    }
    for token, val in tokens.items():
        if val is None:
            main_logger.critical(
                f'Отсутствует обязательная переменная окружения: "{token}". '
                f'Программа принудительно остановлена.'
            )
            return False
    return True


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        exit()

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    old_msg_error = ''

    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            if not homeworks:
                main_logger.debug('Статус домашних работ не изменился.')
            else:
                for homework in homeworks:
                    status_message = parse_status(homework)
                    send_message(bot, status_message)
        except Exception as error:
            msg_error = f'Сбой в работе программы: {error}'
            main_logger.error(msg_error)
            if msg_error != old_msg_error:
                send_message(bot, msg_error)
                old_msg_error = msg_error
        else:
            current_timestamp = response.get('current_date')
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
