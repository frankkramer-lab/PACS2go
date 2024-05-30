class FailedConnectionException(Exception):
    """
    Exception raised for errors in the connection to the data server.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            self.message = None

    def __str__(self):
        if self.message:
            return str(self.message)
        else:
            return 'Connection to data server could not be established.'


class FailedDisconnectException(Exception):
    """
    Exception raised for errors in disconnecting from the data server.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            self.message = None

    def __str__(self):
        if self.message:
            return str(self.message)
        else:
            return 'Disconnect from data server was unsuccessful.'


class UnsuccessfulGetException(Exception):
    """
    Exception raised when a resource cannot be retrieved.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            self.message = None

    def __str__(self):
        if self.message:
            return f'{self.message} could not be retrieved. Try again or contact us.'
        else:
            return 'Resource could not be retrieved. Try again or contact us.'


class UnsuccessfulCreationException(Exception):
    """
    Exception raised when a resource cannot be created.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            self.message = None

    def __str__(self):
        if self.message:
            return f'The creation of {self.message} was unsuccessful. Please make sure that {self.message} does not exist yet. Try again or contact us.'
        else:
            return 'The creation was unsuccessful. Try again or contact us.'


class UnsuccessfulAttributeUpdateException(Exception):
    """
    Exception raised when an attribute update is unsuccessful.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            self.message = None

    def __str__(self):
        if self.message:
            return f'Setting {self.message} was unsuccessful. Try again or contact us.'
        else:
            return 'Attribute update was unsuccessful. Try again or contact us.'


class DownloadException(Exception):
    """
    Exception raised when a download is unsuccessful.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            self.message = None

    def __str__(self):
        return 'Download was unsuccessful. Try again or contact us.'


class UnsuccessfulDeletionException(Exception):
    """
    Exception raised when a deletion is unsuccessful.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            self.message = None

    def __str__(self):
        if self.message:
            return f'Deletion of {self.message} was unsuccessful. Try again or contact us.'
        else:
            return 'Deletion was unsuccessful. Try again or contact us.'


class UnsuccessfulUploadException(Exception):
    """
    Exception raised when an upload is unsuccessful.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            self.message = None

    def __str__(self):
        if self.message:
            return f'Upload of {self.message} was unsuccessful. Try again or contact us.'
        else:
            return 'Upload was unsuccessful. Try again or contact us.'


class WrongUploadFormatException(Exception):
    """
    Exception raised when an upload format is not supported.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            self.message = None

    def __str__(self):
        if self.message:
            return f'Upload of {self.message} was unsuccessful. The format you tried to upload is not supported (yet). Please make sure that all files have valid file extensions.'
        else:
            return 'Format is not allowed. Please contact us.'
