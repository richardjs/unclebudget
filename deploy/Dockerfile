FROM python:3.11-alpine

ENV PATH=/home/unclebudget/.local/bin:$PATH

RUN apk update && \
    apk add poetry

RUN adduser -D -u 38681 unclebudget && \
    mkdir /opt/unclebudget/ && \
    mkdir /opt/unclebudget/data && \
    mkdir /opt/unclebudget/www && \
    chown -R unclebudget:unclebudget /opt/unclebudget

USER unclebudget
WORKDIR /opt/unclebudget

COPY --chown=unclebudget:unclebudget . .

RUN poetry install && \
    poetry add gunicorn

CMD ["sh", "deploy/docker-entrypoint.sh"]
