"""
Custom exceptions for trade validation errors.

These allow the route layer to distinguish between different validation
failure types and return the appropriate HTTP status codes.
"""


class AccountNotFoundError(Exception):
    """Raised when a trade references a non-existent account."""

    def __init__(self, account_id: int, tenant_id: str):
        self.account_id = account_id
        self.tenant_id = tenant_id
        super().__init__(
            f"Account {account_id} not found for tenant {tenant_id}."
        )


class InvalidTradeQuantityError(Exception):
    """Raised when the trade quantity is invalid (e.g. <= 0 or out of range)."""

    def __init__(self, quantity: int, min_qty: int, max_qty: int):
        self.quantity = quantity
        super().__init__(
            f"Invalid trade quantity: {quantity}. "
            f"Must be between {min_qty} and {max_qty}."
        )
