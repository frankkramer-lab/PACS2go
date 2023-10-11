# test_config.py

INSIDE_DOCKER = True  # Change this to False if tests run outside the Docker container

if INSIDE_DOCKER:
    DATABASE_HOST = 'data-structure-db'
    DATABASE_PORT = 5432
else:
    DATABASE_HOST = 'localhost'
    DATABASE_PORT = 5433
