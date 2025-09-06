from shared.exceptions.base import DomainException

class FileException(DomainException):
    pass

class FileNotFound(FileException):
    pass

class FileTypeNotAllowed(FileException):
    pass

class FileSizeExceeded(FileException):
    pass

class FileAccessDenied(FileException):
    pass

class FileUploadFailed(FileException):
    pass