#!/bin/sh

python manage.py migrate
python manage.py collectstatic --no-input
python manage.py check --deploy
gunicorn -b 0.0.0.0:8000 project.wsgi
