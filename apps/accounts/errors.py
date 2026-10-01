class AccountServiceError(Exception):
    """Base error for Account management business rules."""


class AccountPermissionDenied(AccountServiceError):
    pass


class AccountNotFound(AccountServiceError):
    pass


class CannotLockOwnAccount(AccountServiceError):
    pass


class CannotDeleteOwnAccount(AccountServiceError):
    pass


class LastActiveAdminError(AccountServiceError):
    pass


class AccountAlreadyLocked(AccountServiceError):
    pass


class AccountAlreadyActive(AccountServiceError):
    pass


class InvalidAccountRole(AccountServiceError):
    pass


class PasswordValidationError(AccountServiceError):
    pass


class AccountDeleteProtectedError(AccountServiceError):
    pass


class DuplicateAccountEmail(AccountServiceError):
    pass
