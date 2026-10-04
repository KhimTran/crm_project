from django.http import JsonResponse
from ninja import NinjaAPI
from ninja.errors import ValidationError as NinjaValidationError
from ninja.security import SessionAuth

from apps.accounts.api import router as accounts_router
from apps.accounts.api_auth import router as auth_router


api = NinjaAPI(title="CRM API", version="1.0.0", auth=SessionAuth())
api.add_router("/accounts/", accounts_router)
api.add_router("/auth/", auth_router)


@api.exception_handler(NinjaValidationError)
def validation_error(request, exc):
    # Do not echo Pydantic input values, which may contain passwords.
    return JsonResponse({"detail": "Invalid request"}, status=400)
