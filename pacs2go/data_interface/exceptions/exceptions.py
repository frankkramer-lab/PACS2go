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
            return f'{self.message} could not be retrieved. Try again or contact us.'
        else:
            return f'Resource could not be retrieved. Try again or contact us.'


class UnsuccessfulCreationException(Exception):
    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            self.message = None

    def __str__(self):
        if self.message:
            return f'The creation of {self.message} was unsuccessful. Try again or contact us.'
        else:
            return f'The creation of was unsuccessful. Try again or contact us.'


class UnsuccessfulAttributeUpdateException(Exception):
    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            self.message = None

    def __str__(self):
        if self.message:
            return f'Setting {self.message} was unsuccessful. Try again or contact us.'
        else:
            return f'Attribute update was unsuccessful. Try again or contact us.'


class DownloadException(Exception):
    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            self.message = None

    def __str__(self):
        return 'Download was unsuccessful. Try again or contact us.'


class UnsuccessfulDeletionException(Exception):
    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            self.message = None

    def __str__(self):
        if self.message:
            return f'Deletion of {self.message} was unsuccessful. Try again or contact us.'
        else:
            return f'Deletion was unsuccessful. Try again or contact us.'


class UnsuccessfulUploadException(Exception):
    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            self.message = None

    def __str__(self):
        if self.message:
            return f'Upload of {self.message} was unsuccessful. Try again or contact us.'
        else:
            return f'Upload was unsuccessful. Try again or contact us.'


class WrongUploadFormatException(Exception):
    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            self.message = None

    def __str__(self):
        if self.message:
            return f'Upload of {self.message} was unsuccessful. The format you tried to upload is not supported (yet). Please make sure that all files have a valid file extensions.'
        else:
            return f'Format is not allowed. Please contact us.'