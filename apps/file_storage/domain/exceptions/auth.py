from shared.exceptions.base import DomainException

class AuthException(DomainException):
    pass

class InvalidCredentials(AuthException):
    pass

class UserNotFound(AuthException):
    pass

class InsufficientPermissions(AuthException):
    pass

class UserAlreadyExists(AuthException):
    pass