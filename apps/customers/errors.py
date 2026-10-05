class CustomerServiceError(Exception):
    """Base error for Customer management business rules."""


class DuplicateCustomerEmail(CustomerServiceError):
    pass


class DuplicateCustomerPhone(CustomerServiceError):
    pass


class CustomerNotFound(CustomerServiceError):
    pass


class CustomerAlreadyDeleted(CustomerServiceError):
    pass


class CustomerAlreadyLocked(CustomerServiceError):
    pass


class CustomerAlreadyActive(CustomerServiceError):
    pass
