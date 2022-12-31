FROM python:3.10-alpine

ENV PATH=/home/unclebudget/.local/bin:$PATH

RUN adduser -D -u 38681 unclebudget && \
    mkdir /opt/unclebudget/ && \
    mkdir /opt/unclebudget/data && \
    mkdir /opt/unclebudget/www && \
    chown -R unclebudget:unclebudget /opt/unclebudget

USER unclebudget
WORKDIR /opt/unclebudget

COPY requirements.txt .
RUN pip install --user -r requirements.txt gunicorn

COPY --chown=unclebudget:unclebudget deploy/docker-entrypoint.sh .
COPY --chown=unclebudget:unclebudget . .

CMD ["sh", "docker-entrypoint.sh"]
