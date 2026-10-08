from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from apps.accounts.decorators import role_required
from .models import CustomerPreference
from .self_service_choices import CATEGORY_PREFERENCE_TYPE
from .self_service_forms import CustomerCategoryPreferencesForm, CustomerProfileForm
from .self_services import own_customer, update_own_profile


@role_required("CUSTOMER")
@require_http_methods(["GET", "POST"])
def profile(request):
    customer = own_customer(request.user)
    data = request.POST if request.method == "POST" else None
    form = CustomerProfileForm(data, instance=customer)
    preferences = CustomerCategoryPreferencesForm(customer, data)
    if request.method == "POST":
        profile_valid = form.is_valid()
        preferences_valid = preferences.is_valid()
        if profile_valid and preferences_valid:
            try:
                update_own_profile(request.user, profile_data=form.cleaned_data,
                                   category_ids=preferences.cleaned_data["categories"],
                                   remove_preference_ids=preferences.cleaned_data["remove_preferences"])
            except ValidationError as exc:
                for field, errors in exc.message_dict.items():
                    target = preferences if field in preferences.fields else form
                    target.add_error(field if field in target.fields else None, errors)
            else:
                messages.success(request, "Đã cập nhật hồ sơ và sở thích.")
                return redirect("customers:profile")
    other_preferences = CustomerPreference.objects.filter(customer=customer).exclude(
        preference_type=CATEGORY_PREFERENCE_TYPE,
    ).order_by("preference_id")
    return render(request, "customers/profile.html", {
        "form": form, "preferences": preferences, "customer": customer, "other_preferences": other_preferences,
    })
