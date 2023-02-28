class FailedConnectionException(Exception):
    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            self.message = None

    def __str__(self):
        if self.message:
            return str(self.message)
        else:
            # Messages aim at providing medical professionals comprehensive error messages
            return 'Connection to data server could not be established.'


class FailedDisconnectException(Exception):
    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            self.message = None

    def __str__(self):
        if self.message:
            return str(self.message)
        else:
            # Messages aim at providing medical professionals comprehensive error messages
            return 'Disconnect from data server was unsuccessful.'


class UnsuccessfulGetException(Exception):
    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            self.message = None

    def __str__(self):
        if self.message:
            return str(self.message)
        else:
            return f'{self.message} could not be retrieved. Try again or contact us.'


class UnsuccessfulProjectCreationException(Exception):
    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            self.message = None

    def __str__(self):
        if self.message:
            return str(self.message)
        else:
            return f'The creation of a new project called {self.message} was unsuccessful. Try again or contact us.'


class UnsuccessfulAttributeUpdateException(Exception):
    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            self.message = None

    def __str__(self):
        if self.message:
            return str(self.message)
        else:
            return f'Setting {self.message} was unsuccessful. Try again or contact us.'


class DownloadException(Exception):
    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            self.message = None

    def __str__(self):
        if self.message:
            return str(self.message)
        else:
            return 'Download was unsuccessful. Try again or contact us.'


class UnsuccessfulDeletionException(Exception):
    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            self.message = None

    def __str__(self):
        if self.message:
            return str(self.message)
        else:
            return f'Deletion of {self.message} was unsuccessful. Try again or contact us.'


class UnsuccessfulUploadException(Exception):
    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            self.message = None

    def __str__(self):
        if self.message:
            return str(self.message)
        else:
            return f'Upload of {self.message} was unsuccessful. Try again or contact us.'
