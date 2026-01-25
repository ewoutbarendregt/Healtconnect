"""
Custom exceptions for HealthConnect automation.
"""

class WorkflowError(Exception):
    """Base exception for workflow errors."""
    pass


class VerificationError(WorkflowError):
    """Raised when UI verification fails."""
    pass


class StuckLoopError(WorkflowError):
    """Raised when computer use appears stuck."""
    pass


class SafetyError(WorkflowError):
    """Raised when safety check fails."""
    pass


class ExtractionError(WorkflowError):
    """Raised when metadata extraction fails."""
    pass


class ConversionError(WorkflowError):
    """Raised when PDF conversion fails."""
    pass


class UploadError(WorkflowError):
    """Raised when file upload fails."""
    pass
