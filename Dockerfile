FROM python:3.8-slim-buster

WORKDIR /app/

COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . /app/

# Update Python pip
RUN python -m pip install pip --upgrade

# Install pacs2go from local git repo
RUN pip install -e .