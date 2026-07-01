"""
Custom exception classes for trade validation errors.

These exceptions allow the route layer to distinguish between different
validation failure types and return appropriate HTTP status codes instead
of a generic 400 for every error.
"""


class TradeValidationError(Exception):
    """Base class for trade validation errors."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class AccountNotFoundError(TradeValidationError):
    """Raised when a trade references a non-existent account."""
    pass


class InvalidTradeQuantityError(TradeValidationError):
    """Raised when the trade quantity is outside the allowed range."""
    pass


class SecurityNotFoundError(TradeValidationError):
    """Raised when the trade references a non-existent security/ticker."""
    pass
