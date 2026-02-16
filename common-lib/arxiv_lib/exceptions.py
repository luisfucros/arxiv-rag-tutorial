class ArxivServiceError(Exception):
    """
    Base class for api service errors.
    """
    pass


class APICallFailed(ArxivServiceError):
    """
    Thrown when a call to an API fails.
    """
    pass


class ConflictError(ArxivServiceError):
    """
    Thrown when there is a conflict in the operation.
    """
    pass


class EntityAlreadyExists(ConflictError):
    """
    Thrown when trying to create an object that already exists.
    """
    pass


class EntityNotFound(ArxivServiceError):
    """
    Thrown when the requested object does not exist.
    """
    pass


class ServiceNotAvailable(ArxivServiceError):
    """
    Thrown when a service is not available.
    """
    pass
