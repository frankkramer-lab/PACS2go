FROM python:3.11.3-slim-buster

WORKDIR /app/

# Update Python pip

RUN python -m pip install --upgrade pip

COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . /app/


# Install pacs2go from local git repo
RUN pip install -e .