"""Custom exception types for the Multimodal Evidence SDK."""

class MultimodalSDKError(Exception):
    """Base exception for all SDK errors."""
    pass


class ConfigurationError(MultimodalSDKError):
    """Raised when configuration, paths, or keys are missing or invalid."""
    pass


class ImageValidationError(MultimodalSDKError):
    """Raised when input images are corrupt, unreadable, or missing."""
    pass


class APIError(MultimodalSDKError):
    """Raised when the Gemini API returns errors or fails all retries."""
    pass


class ResponseValidationError(MultimodalSDKError):
    """Raised when Gemini responses fail model validation or allowed enum ranges."""
    pass
