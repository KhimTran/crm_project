"""Coordinate HTTP requests and restore across workers on the same host.

The lock file must remain in place. External jobs and direct database clients
must be stopped by the operator; they do not participate in this HTTP guard.
"""

import errno
import logging
from contextlib import ExitStack, contextmanager
from contextvars import ContextVar

from django.http import HttpResponse
from django.urls import reverse

from .backup_service import get_backup_dir


class DatabaseMaintenanceError(RuntimeError):
    pass


_request_lock = ContextVar("database_request_lock", default=None)
logger = logging.getLogger(__name__)


def recovery_marker_path():
    return get_backup_dir() / ".restore-recovery.json"


@contextmanager
def database_access(*, exclusive=False):
    """Nonblocking OS reader/writer lock; closing the handle releases it."""
    current = _request_lock.get()
    if current is not None:
        if exclusive and not current:
            raise DatabaseMaintenanceError("Restore requires an exclusive maintenance request.")
        yield
        return

    with (get_backup_dir() / ".maintenance.lock").open("a+b") as lock_file:
        import os

        if os.name == "nt":
            import ctypes
            import msvcrt
            from ctypes import wintypes

            class Overlapped(ctypes.Structure):
                _fields_ = [("Internal", ctypes.c_size_t), ("InternalHigh", ctypes.c_size_t),
                            ("Offset", wintypes.DWORD), ("OffsetHigh", wintypes.DWORD),
                            ("hEvent", wintypes.HANDLE)]

            kernel = ctypes.WinDLL("kernel32", use_last_error=True)
            kernel.LockFileEx.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.DWORD,
                                         wintypes.DWORD, wintypes.DWORD, ctypes.POINTER(Overlapped)]
            kernel.LockFileEx.restype = wintypes.BOOL
            overlapped = Overlapped()
            handle = msvcrt.get_osfhandle(lock_file.fileno())
            if not kernel.LockFileEx(handle, 1 | (2 if exclusive else 0), 0, 1, 0, ctypes.byref(overlapped)):
                error = ctypes.get_last_error()
                if error not in (32, 33, 158):
                    raise OSError(error, "Unable to acquire database maintenance lock")
                raise DatabaseMaintenanceError("Other requests are active. Retry during the maintenance window.")
        else:
            import fcntl

            try:
                fcntl.flock(lock_file, (fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH) | fcntl.LOCK_NB)
            except OSError as exc:
                if exc.errno not in (errno.EACCES, errno.EAGAIN):
                    raise
                raise DatabaseMaintenanceError("Other requests are active. Retry during the maintenance window.") from None

        token = _request_lock.set(exclusive)
        try:
            if recovery_marker_path().exists():
                raise DatabaseMaintenanceError("Recovery is required before database access can resume.")
            yield
        finally:
            _request_lock.reset(token)


class DatabaseMaintenanceMiddleware:
    """Run first, so even session/auth writes finish before a restore starts."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        exclusive = request.method == "POST" and request.path_info == reverse("database_restore")
        with ExitStack() as stack:
            try:
                stack.enter_context(database_access(exclusive=exclusive))
            except (DatabaseMaintenanceError, OSError) as exc:
                if exclusive:
                    logger.warning("database_restore request_blocked reason=%s", type(exc).__name__)
                response = HttpResponse(
                    "Database maintenance is in progress or recovery is required. "
                    "Contact the administrator; see the server log and database/backups/.restore-recovery.json.",
                    status=503,
                    content_type="text/plain; charset=utf-8",
                )
                response["Retry-After"] = "60"
                return response
            return self.get_response(request)
