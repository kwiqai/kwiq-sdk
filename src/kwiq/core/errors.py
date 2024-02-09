class TaskException(Exception):
    """Base exception for task errors."""


class ValidationError(Exception):
    """Raised when input data validation fails."""


class ProcessingError(Exception):
    """Raised when an error occurs during the processing of a task."""
