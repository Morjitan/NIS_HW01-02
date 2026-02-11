class DomainValidationError(ValueError):
    """Raised when domain invariants are violated."""


class NotFoundError(LookupError):
    """Raised when an entity is not found or not accessible."""
