FROM python:3.6.9

WORKDIR /app/
# copy our requirements.txt file and install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . /app/

# exposing our app port in docker internal network
EXPOSE 5000