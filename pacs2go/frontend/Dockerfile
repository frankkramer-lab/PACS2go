FROM python:3.6.9-slim

WORKDIR /app/

COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . /app/

RUN pip install -e pacs2go