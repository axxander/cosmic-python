FROM python:3.9-slim-buster

COPY requirements.txt /tmp
RUN pip install -r /tmp/requirements.txt

RUN mkdir -p /opt
COPY *.py /opt

WORKDIR /opt

ENV FLASK_APP=flask_app.py FLASK_DEBUG=1 PYTHONBUFFERED=1

CMD flask run --host=0.0.0.0 --port=80