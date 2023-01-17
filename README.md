# homework_bot
Бот ассистент для отслеживания изменения статуса отправленных на проверку работ с использованием API Яндекс.Практикум.

### Технологии:
Python 3.7, python-telegram-bot, Requests, Pytest

### Как запустить проект:
Клонировать репозиторий и перейти в него в командной строке:

```
https://github.com/BiftAL/homework_bot.git
```

```
cd homework_bot
```

Cоздать и активировать виртуальное окружение:

```
python -m venv venv
```

Для Windows:
```
source venv/Scripts/activate
```
Для Linux и MacOS:
```
source venv/bin/activate
```
Переименовать и отредактировать в корне проекта файл env.example в .env

python -m pip install --upgrade pip

Обновить менеджер пакетов
```
python -m pip install --upgrade pip
```

Установить зависимости из файла requirements.txt:

```
pip install -r requirements.txt
```
Для запуска тестов выполнить команду:

```
pytest
```
Для запуска модуля выполнить команду:

```
python homework.py 
```
