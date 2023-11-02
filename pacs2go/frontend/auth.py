import requests
from flask import session
from flask_login import UserMixin

from pacs2go.frontend.helpers import server_url
from pacs2go.data_interface.logs.config_logging import logger


class User(UserMixin):
    def __init__(self, username, session_id):
        self.id = username
        self.session_id = session_id

    def get_id(self):
        return self.id

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False


class XNATAuthBackend:
    def authenticate(self, username, password):
        # Send request to XNAT server to authenticate user
        data = {"username": username, "password": password}
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        response = requests.post(
            server_url + "/data/services/auth", data=data, headers=headers)
        if response.status_code == 200:
            # Login was successful
            session_id = response.text
            logger.info(f"User {username} authenticated successfully.")
            return User(username, session_id)
        else:
            # Login failed
            return None

    def get_user(self, username):
        # Check if user is logged in
        session_id = session.get("session_id")
        if session_id is not None:
            # User is logged in, return user object
            return User(username, session_id)
        else:
            # User is not logged in
            return None
