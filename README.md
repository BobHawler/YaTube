# YaTube Project

YaTube - это социальная сеть для публикации личных дневников.
На сайте можно публиковать посты, общаться в тематических группах, подписываться на авторов и комментировать их записи.

### Технологии
```
Python 3.9 Django 4.2
```
### Как запустить проект:

Клонировать репозиторий и перейти в него в командной строке:
```
git clone git@github.com:BobHawler/YaTube.git
cd YaTube/
```
### Cоздать и активировать виртуальное окружение:
```
python3 -m venv venv
source venv/Scripts/activate
python3 -m pip install --upgrade pip
```
### Установить зависимости из файла requirements.txt:
```
pip install -r requirements.txt
```
### Выполнить миграции:
```
python3 manage.py migrate
```
### Запустить проект:
```
python3 manage.py runserver
```

Автор:
Анатолий Коновалов (BobHawler)
