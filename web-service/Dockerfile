FROM python:3.6.9

# Copy code from local
COPY . .

#Install all requirements in the Docker Image
RUN pip install -r ./requirements.txt

# exposing our app port in docker internal network
EXPOSE 5000
# run the application
CMD gunicorn --bind 0.0.0.0:8000 wsgi:app