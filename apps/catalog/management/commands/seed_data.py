import os
from decimal import Decimal

from django.conf import settings
from django.core.management.base import CommandError
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import Account
from apps.catalog.models import Brand, Category, Product, Supplier
from apps.customers.models import Customer, CustomerPreference
from apps.feedback.models import Feedback
from apps.surveys.models import Survey, SurveyOption, SurveyQuestion, SurveyRecipient, SurveyResponse, SurveyAnswer


SUPPLIERS = (
    ("SUP001", "Yonex Vietnam"), ("SUP002", "Lining Sports"),
    ("SUP003", "Victor Distribution"), ("SUP004", "Mizuno Sports"),
    ("SUP005", "Kawasaki Badminton"), ("SUP006", "Apacs Vietnam"),
    ("SUP007", "Fleet Sports"), ("SUP008", "Protech Badminton"),
)


class Command(BaseCommand):
    help = "Create repeatable supplier, product and survey demo data"

    @transaction.atomic
    def handle(self, *args, **options):
        demo_password = os.environ.get("CRM_DEMO_PASSWORD")
        if not demo_password:
            if not settings.DEBUG:
                raise CommandError("Set CRM_DEMO_PASSWORD before seeding accounts outside DEBUG mode.")
            demo_password = "DemoPass!2026"  # Local demo accounts only; never use for real accounts.
        admin = Account.objects.filter(email="demo-admin@example.test").first()
        if admin is None:
            admin = Account.objects.create_superuser("demo-admin@example.test", demo_password)
        customer_account = Account.objects.filter(email="demo-customer@example.test").first()
        if customer_account is None:
            customer_account = Account.objects.create_user("demo-customer@example.test", demo_password)
        customer, _ = Customer.objects.get_or_create(
            account=customer_account, defaults={"full_name": "Demo customer"}
        )
        CustomerPreference.objects.get_or_create(
            customer=customer, preference_type="CATEGORY", preference_value="Badminton rackets"
        )
        suppliers = []
        for code, name in SUPPLIERS:
            supplier, _ = Supplier.objects.get_or_create(supplier_code=code, defaults={"supplier_name": name})
            suppliers.append(supplier)
        category, _ = Category.objects.get_or_create(category_name="Badminton rackets")
        brand, _ = Brand.objects.get_or_create(brand_name="Demo brand")
        products = []
        for index, supplier in enumerate(suppliers, 1):
            product, _ = Product.objects.get_or_create(product_name=f"Demo racket {index}", defaults={
                "category": category, "brand": brand, "supplier": supplier, "price": Decimal("100000.00")
            })
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
        self.stdout.write(self.style.SUCCESS("Demo accounts, suppliers, products and survey data ready."))
