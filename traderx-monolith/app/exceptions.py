"""
Custom exception classes for trade validation errors.

These exceptions allow the route layer to return specific HTTP status codes
instead of a generic 400 for all validation failures.
"""


class AccountNotFoundError(Exception):
    """Raised when a trade references an account that does not exist."""

    def __init__(self, account_id: int, tenant_id: str):
        self.account_id = account_id
        self.tenant_id = tenant_id
        super().__init__(
            f"Account {account_id} not found for tenant {tenant_id}."
        )


class InvalidQuantityError(Exception):
    """Raised when a trade has an invalid quantity."""

    def __init__(self, quantity: int, message: str):
        self.quantity = quantity
        super().__init__(message)
