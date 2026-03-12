"""
Custom exception classes for trade validation errors.

These exceptions allow the route layer to distinguish between different
validation failure types and return appropriate HTTP status codes.
"""


class TradeValidationError(Exception):
    """Base exception for trade validation failures."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class AccountNotFoundError(TradeValidationError):
    """Raised when a trade references a non-existent account."""
    pass


class InvalidTradeQuantityError(TradeValidationError):
    """Raised when the trade quantity is invalid (e.g. zero, negative, or out of range)."""
    pass
