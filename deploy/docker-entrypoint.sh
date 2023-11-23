#!/bin/sh

poetry run python manage.py migrate
poetry run python manage.py createcachetable
poetry run python manage.py collectstatic --no-input
poetry run python manage.py check --deploy
poetry run gunicorn -b 0.0.0.0:8000 project.wsgi
