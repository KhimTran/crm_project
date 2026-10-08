from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from apps.accounts.decorators import role_required
from .models import CustomerPreference
from .self_service_forms import CustomerPreferenceFormSet, CustomerProfileForm
from .self_services import own_customer, update_own_profile


@role_required("CUSTOMER")
@require_http_methods(["GET", "POST"])
def profile(request):
    customer = own_customer(request.user)
    data = request.POST if request.method == "POST" else None
    form = CustomerProfileForm(data, instance=customer)
    preferences = CustomerPreferenceFormSet(
        data, prefix="preferences", queryset=CustomerPreference.objects.filter(customer=customer).order_by("preference_id"),
    )
    if request.method == "POST":
        profile_valid = form.is_valid()
        preferences_valid = preferences.is_valid()
        if profile_valid and preferences_valid:
            items = []
            for preference_form in preferences:
                if preference_form.cleaned_data:
                    item = dict(preference_form.cleaned_data)
                    preference = item.pop("preference_id", None)
                    item["preference_id"] = preference.pk if preference else None
                    items.append(item)
            update_own_profile(request.user, profile_data=form.cleaned_data, preferences=items)
            messages.success(request, "Đã cập nhật hồ sơ và sở thích.")
            return redirect("customers:profile")
    return render(request, "customers/profile.html", {"form": form, "preferences": preferences, "customer": customer})
