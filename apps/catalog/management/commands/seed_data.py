import os
from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import Account, Role
from apps.accounts.provisioning import ensure_admin_profile, ensure_staff_profile
from apps.catalog.models import Brand, Category, Product
from apps.customers.models import Customer, CustomerPreference
from apps.customers.seed import seed_customers
from apps.feedback.models import Feedback
from apps.feedback.seed import seed_feedbacks
from apps.surveys.models import Survey, SurveyAnswer, SurveyOption, SurveyQuestion, SurveyRecipient, SurveyResponse


class Command(BaseCommand):
    help = "Create repeatable product, CRM and survey demo data"

    @transaction.atomic
    def handle(self, *args, **options):
        demo_password = os.environ.get("CRM_DEMO_PASSWORD")
        if not demo_password:
            if not settings.DEBUG:
                raise CommandError("Set CRM_DEMO_PASSWORD before seeding accounts outside DEBUG mode.")
            demo_password = "DemoPass!2026"  # Local demo accounts only; never use for real accounts.

        # Ensure standard roles
        Role.objects.get_or_create(role_code="ADMIN", defaults={"role_name": "Quản trị viên hệ thống"})
        Role.objects.get_or_create(role_code="MANAGER", defaults={"role_name": "Quản lý kinh doanh & CRM"})
        Role.objects.get_or_create(role_code="CUSTOMER", defaults={"role_name": "Khách hàng"})

        admin = Account.objects.filter(email="demo-admin@example.test").first()
        if admin is None:
            admin = Account.objects.create_superuser("demo-admin@example.test", demo_password)
        ensure_admin_profile(admin.pk, admin_code="AD0001", full_name="System Administrator")

        customer = Account.objects.filter(email="demo-customer@example.test").first()
        if customer is None:
            customer = Account.objects.create_user("demo-customer@example.test", demo_password, full_name="Demo customer")
        CustomerPreference.objects.get_or_create(
            customer=customer, preference_type="CATEGORY", preference_value="Badminton rackets"
        )

        category, _ = Category.objects.get_or_create(category_name="Badminton rackets")
        brand, _ = Brand.objects.get_or_create(brand_name="Demo brand")
        products = []
        for index in range(1, 9):
            product, _ = Product.objects.get_or_create(
                product_name=f"Demo racket {index}",
                defaults={
                    "category": category,
                    "brand": brand,
                    "price": Decimal("100000.00"),
                },
            )
            products.append(product)

        Feedback.objects.get_or_create(
            customer=customer, product=products[0],
            defaults={"rating": 5, "content": "Good racket", "status": "NEW"},
        )
        survey, _ = Survey.objects.get_or_create(
            title="Demo badminton survey", defaults={"created_by": admin, "status": "ACTIVE"}
        )
        question, _ = SurveyQuestion.objects.get_or_create(
            survey=survey, question_text="How was your shopping experience?",
            defaults={"question_type": "SINGLE_CHOICE", "is_required": True}
        )
        option, _ = SurveyOption.objects.get_or_create(question=question, option_text="Good")
        recipient, _ = SurveyRecipient.objects.get_or_create(
            survey=survey, customer=customer, defaults={"status": "SENT"}
        )
        now = timezone.now()
        response, _ = SurveyResponse.objects.get_or_create(
            recipient=recipient,
            defaults={"status": "SUBMITTED", "started_at": now, "submitted_at": now}
        )
        SurveyAnswer.objects.get_or_create(response=response, question=question, defaults={"option": option})
        if response.status == "SUBMITTED" and recipient.status != "COMPLETED":
            recipient.status = "COMPLETED"
            recipient.completed_at = now
            recipient.save(update_fields=["status", "completed_at"])

        # tv4: khách hàng demo kh01…kh40 + phản hồi demo (apps/customers/seed.py, apps/feedback/seed.py)
        new_customers = seed_customers()
        new_feedbacks = seed_feedbacks(handler=admin)
        self.stdout.write(f"TV4 demo: {new_customers} new customers, {new_feedbacks} new feedbacks.")
        self.stdout.write(self.style.SUCCESS("Demo accounts, products and survey data ready."))
