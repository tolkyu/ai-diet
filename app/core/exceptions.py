from fastapi import HTTPException, status


class AppException(Exception):
    """Base application exception."""
    def __init__(self, message: str, code: str = "APP_ERROR") -> None:
        self.message = message
        self.code = code
        super().__init__(message)


class UserNotFoundError(AppException):
    def __init__(self, identifier: str | int) -> None:
        super().__init__(f"User not found: {identifier}", "USER_NOT_FOUND")


class UserNotRegisteredError(AppException):
    def __init__(self) -> None:
        super().__init__("User has not completed registration", "USER_NOT_REGISTERED")


class GoalNotFoundError(AppException):
    def __init__(self) -> None:
        super().__init__("No active goal found for user", "GOAL_NOT_FOUND")


class QuotaExceededError(AppException):
    def __init__(self, quota_type: str, limit: int) -> None:
        super().__init__(
            f"Daily {quota_type} limit of {limit} reached. Upgrade to Premium for unlimited access.",
            "QUOTA_EXCEEDED",
        )


class AIServiceError(AppException):
    def __init__(self, message: str = "AI service temporarily unavailable") -> None:
        super().__init__(message, "AI_SERVICE_ERROR")


class StorageError(AppException):
    def __init__(self, message: str = "File storage error") -> None:
        super().__init__(message, "STORAGE_ERROR")


class ValidationError(AppException):
    def __init__(self, field: str, message: str) -> None:
        super().__init__(f"Validation error on {field}: {message}", "VALIDATION_ERROR")
        self.field = field


# ─── HTTP exceptions for FastAPI ───────────────────────────────────────────────

def raise_not_found(detail: str = "Not found") -> None:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


def raise_unauthorized(detail: str = "Unauthorized") -> None:
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


def raise_forbidden(detail: str = "Forbidden") -> None:
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)
