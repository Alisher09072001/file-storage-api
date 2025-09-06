class DomainException(Exception):
    pass

class InfrastructureException(Exception):
    pass

class ValidationException(DomainException):
    pass

class NotFoundError(DomainException):
    pass

class AccessDeniedError(DomainException):
    pass