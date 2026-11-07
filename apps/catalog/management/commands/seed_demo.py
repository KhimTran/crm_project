"""The small, repeatable handoff dataset. Never deletes or resets existing rows."""
from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import Account, Role
from apps.catalog.models import Brand, Category, Product
from apps.catalog.management.commands.seed_catalog import BRANDS, CATEGORIES, PRODUCTS, IMAGES, INACTIVE_PRODUCTS
from apps.customers.models import CustomerPreference
from apps.feedback.models import Feedback
from apps.feedback.seed import CONTENTS, CATEGORY_KINDS
from apps.surveys.configuration import populate_questionnaire
from apps.surveys.models import Survey, SurveyRecipient, SurveyResponse, SurveyAnswer
from apps.surveys.services import send_survey, start_survey, submit_survey, _check_answer_shapes

PASSWORD = "Crm@2026"  # Public fictional demo accounts only.
MARK = "CRM_FINAL_DEMO_V1"
NAMES = ("Nguyễn Minh Anh", "Trần Hoàng Nam", "Lê Thảo Vy", "Phạm Quốc Huy", "Hoàng Ngọc Hà",
         "Võ Đức Minh", "Đặng Thu Trang", "Bùi Thanh Sơn", "Đỗ Hải Yến", "Hồ Gia Bảo",
         "Ngô Mai Chi", "Dương Tuấn Kiệt", "Lý Bích Ngọc", "Đinh Văn Phúc", "Mai Khánh Linh")
TITLES = (
    "Nhu cầu vợt nhẹ cho người mới", "Mẫu giày giảm chấn sắp nhập", "Ý tưởng giải giao lưu khách hàng",
    "Hài lòng sau mua vợt cầu lông", "Trải nghiệm tư vấn chọn giày", "Nhu cầu đan cước cuối tuần",
    "Thương hiệu khách hàng yêu thích", "Mức giá phụ kiện phù hợp", "Ưu đãi dành cho câu lạc bộ",
    "Chương trình thành viên thân thiết", "Chất lượng đóng gói và giao hàng", "Dịch vụ đổi trả sản phẩm",
    "Trải nghiệm mua hàng tại cửa hàng", "Nhu cầu ống cầu tập luyện", "Chất lượng cước và quấn cán",
    "Mua sắm quần áo thi đấu", "Góp ý tư vấn thông số vợt", "Tổng kết hoạt động giao lưu cầu lông",
)
COMMENTS = (
    "Vợt chắc tay, thông số đúng mô tả và phù hợp trình độ của tôi.",
    "Giày bám sân tốt, mong cửa hàng bổ sung thêm cỡ lớn.",
    "Giá hợp lý, tôi muốn có ưu đãi khi mua cùng đồng đội.",
    "Đóng gói cẩn thận nhưng giao hàng còn chậm một ngày.",
    "Nhân viên tư vấn rõ ràng, giúp tôi chọn được sản phẩm phù hợp.",
    "Cước đan đều và đúng số kg, mong có lịch hẹn lấy nhanh.",
    "Đổi cỡ giày thuận tiện, nhân viên hỗ trợ rất nhiệt tình.",
    "Quấn cán hơi nhanh mòn, cửa hàng nên có thêm lựa chọn bền hơn.",
    "Áo thoáng khí, đường may tốt và mặc thoải mái khi thi đấu.",
    "Ống cầu có vài quả nhanh hỏng, mong được kiểm tra trước khi giao.",
)


def demo_emails():
    return [f"admin{i}@demo.test" for i in range(1, 3)] + [
        f"manager{i}@demo.test" for i in range(1, 4)] + [f"cus{i}@demo.test" for i in range(1, 16)]


def answer_payload(survey, variation):
    rows = []
    for question in survey.surveyquestion_set.order_by("sort_order"):
        options = list(question.surveyoption_set.order_by("sort_order"))
        base = {"question_id": question.pk}
        if question.question_type in ("SINGLE_CHOICE", "MULTI_CHOICE"):
            selected = [options[variation % len(options)]]
            if question.question_type == "MULTI_CHOICE":
                selected.append(options[(variation + 1) % len(options)])
            for option in selected:
                row = dict(base, option_id=option.pk)
                if option.pk == question.config.get("other_option_id"):
                    row["answer_text"] = "Apacs"
                rows.append(row)
        elif question.question_type == "MATRIX":
            rows.extend(dict(base, option_id=o.pk, rating_value=1 + (variation + i) % 5)
                        for i, o in enumerate(options))
        elif question.question_type == "RATING":
            rows.append(dict(base, rating_value=question.config["rating_max"] - variation % 3))
        else:
            rows.append(dict(base, answer_text=COMMENTS[variation % len(COMMENTS)]))
    return rows


def feedback_content(product, index):
    sentiment = "good" if index % 5 >= 3 else "mid" if index % 5 == 2 else "bad"
    texts = CONTENTS[CATEGORY_KINDS.get(product.category.category_name, "racket")][sentiment]
    service = ("Tư vấn rõ ràng và phù hợp trình độ chơi.", "Mong có ưu đãi giá cho câu lạc bộ.",
               "Giao hàng chậm hơn lịch hẹn một ngày.", "Dịch vụ đan cước đúng số kg đã yêu cầu.",
               "Đổi trả được hướng dẫn rõ ràng.", "Mong có thêm phụ kiện tặng kèm.")
    return f"{texts[index % len(texts)]} {service[index % len(service)]} Lần mua {index + 1:02d}."


def validate_demo_surveys():
    """Fail rather than announce success for a partial or inconsistent dataset."""
    for i, title in enumerate(TITLES):
        survey = Survey.objects.get(title=title, description=MARK)
        expected = (0, 0, "DRAFT") if i < 3 else (5, 3, "ACTIVE") if i < 10 else (7, 5, "CLOSED")
        recipients = survey.surveyrecipient_set.all()
        responses = SurveyResponse.objects.filter(recipient__survey=survey)
        if (recipients.count(), responses.filter(status='SUBMITTED').count(), survey.status) != expected:
            raise CommandError(f"Demo survey has changed or is incomplete: {title}; existing data preserved.")
        questions = {q.pk: q for q in survey.surveyquestion_set.all()}
        if len(questions) != 8 or {q.question_type for q in questions.values()} != {
                'SINGLE_CHOICE', 'MULTI_CHOICE', 'RATING', 'TEXT', 'MATRIX'}:
            raise CommandError('Demo questionnaire is incomplete; existing data preserved.')
        if responses.count() != expected[1] or recipients.exclude(
                customer__email__in=demo_emails()[5:], customer__role__role_code='CUSTOMER').exists():
            raise CommandError('Unexpected demo response or audience; existing data preserved.')
        for response in responses.select_related('recipient__customer'):
            recipient = response.recipient
            if recipient.customer.email not in demo_emails()[5:] or recipient.status != 'COMPLETED':
                raise CommandError('Invalid demo recipient/customer relationship.')
            if not (recipient.sent_at <= recipient.opened_at <= response.started_at <= response.submitted_at == recipient.completed_at):
                raise CommandError('Inconsistent demo response timestamps.')
            payload = []
            for answer in response.surveyanswer_set.all():
                row = {'question_id': answer.question_id}
                row.update({key:value for key,value in {'option_id':answer.option_id,
                    'rating_value':answer.rating_value, 'answer_text':answer.answer_text}.items() if value is not None})
                payload.append(row)
            if not {q.pk for q in questions.values() if q.is_required}.issubset({a['question_id'] for a in payload}):
                raise CommandError('Missing required demo answers.')
            if any(a['question_id'] not in questions for a in payload):
                raise CommandError('Demo answer belongs to a different survey.')
            _check_answer_shapes(questions, payload)


class Command(BaseCommand):
    help = "Seed 20 accounts, 15 customers, 20 feedbacks and 18 surveys without replacing existing data."

    @transaction.atomic
    def handle(self, *args, **options):
        now = timezone.now()
        accounts = []
        for index, email in enumerate(demo_emails()):
            role = "ADMIN" if index < 2 else "MANAGER" if index < 5 else "CUSTOMER"
            Role.objects.get_or_create(role_code=role, defaults={"role_name": role})
            account = Account.objects.filter(email=email).first()
            if account is not None:
                if account.role_code != role or account.status != "ACTIVE" or not account.check_password(PASSWORD):
                    raise CommandError(f"Reserved demo email conflicts with existing account: {email}; no changes committed.")
            else:
                customer_index = index - 5
                account = Account.objects.create_user(email, PASSWORD, role=role, full_name=(
                    NAMES[customer_index] if role == "CUSTOMER" else f"Demo {role.title()} {index + 1}"),
                    phone=f"090000{index:04d}", date_of_birth=date(
                        [2010, 2005, 2000, 1995, 1988, 1980, 1970, 1965][customer_index % 8]
                        if role == "CUSTOMER" else 1990, 3, 12),
                    gender=["FEMALE", "MALE", "OTHER"][index % 3],
                    address=f"{index + 1} Đường Thể Thao, TP. Hồ Chí Minh (giả lập)",
                    playing_level=["BEGINNER", "RECREATIONAL", "COMPETITIVE"][index % 3])
                Account.objects.filter(pk=account.pk).update(created_at=now - timedelta(days=index * 12))
            accounts.append(account)
        customers, handlers = accounts[5:], accounts[2:5]

        # Reuse catalog definitions, but never normalize or overwrite existing catalog data.
        categories = {name: Category.objects.get_or_create(category_name=name,
                      defaults={"description": description, "status": "ACTIVE"})[0] for name, description in CATEGORIES}
        brands = {name: Brand.objects.get_or_create(brand_name=name,
                  defaults={"description": description, "status": "ACTIVE"})[0] for name, description in BRANDS}
        for category, brand, name, description, price in PRODUCTS:
            Product.objects.get_or_create(product_name=name, defaults={"category": categories[category],
                "brand": brands[brand], "description": description, "price": Decimal(price),
                "status": "INACTIVE" if name in INACTIVE_PRODUCTS else "ACTIVE", "image_url": IMAGES.get(name, "")})
        products = list(Product.objects.filter(product_name__in=[row[2] for row in PRODUCTS])
                        .select_related('category').order_by("product_name"))
        if not products:
            raise CommandError("No active products available for demo feedback.")
        for i, customer in enumerate(customers):
            for kind, value in (("BRAND", BRANDS[i % len(BRANDS)][0]),
                                ("FAVORITE_BRAND", BRANDS[i % len(BRANDS)][0]),
                                ("CATEGORY", CATEGORIES[i % len(CATEGORIES)][0])):
                CustomerPreference.objects.get_or_create(customer=customer, preference_type=kind, preference_value=value)
        for i in range(20):
            done = i >= 8
            feedback, created = Feedback.objects.get_or_create(customer=customers[i % 15],
                content=feedback_content(products[i % len(products)], i),
                defaults={"product": products[i % len(products)], "rating": 1 + i % 5,
                          "status": "RESOLVED" if done else "NEW",
                          "manager_note": "Đã liên hệ, tư vấn và thống nhất phương án hỗ trợ khách hàng." if done else None,
                          "handled_by": handlers[i % 3] if done else None,
                          "resolved_at": now - timedelta(days=2 + i % 5) if done else None})
            if created:
                Feedback.objects.filter(pk=feedback.pk).update(created_at=now - timedelta(days=14 + i))
        for i, title in enumerate(TITLES):
            status = "DRAFT" if i < 3 else "ACTIVE" if i < 10 else "CLOSED"
            existing = Survey.objects.filter(title=title).first()
            if existing:
                if existing.description != MARK or existing.created_by_id not in [a.pk for a in handlers]:
                    raise CommandError(f"Survey title conflicts with non-demo data: {title}")
                continue
            invited, completed = (0, 0) if status == "DRAFT" else (5, 3) if status == "ACTIVE" else (7, 5)
            audience = [customers[(i + j) % 15] for j in range(invited)]
            survey = Survey.objects.create(title=title, description=MARK, objective=[
                "SATISFACTION", "NEW_PRODUCT", "SHOPPING_NEEDS", "OTHER"][i % 4],
                status="DRAFT", created_by=handlers[i % 3], start_at=now - timedelta(days=21),
                end_at=now + timedelta(days=365), audience={"audience": "pick", "customer_ids": [c.pk for c in audience]}
                if invited else {"audience": "all"})
            populate_questionnaire(survey)
            if invited:
                send_survey(handlers[i % 3], survey, [c.pk for c in audience])
                for j, customer in enumerate(audience):
                    recipient = SurveyRecipient.objects.get(survey=survey, customer=customer)
                    sent = now - timedelta(days=20)
                    SurveyRecipient.objects.filter(pk=recipient.pk).update(sent_at=sent)
                    if j >= completed:
                        continue
                    response, _ = start_survey(customer, recipient.pk)
                    if not submit_survey(customer, recipient.pk, answer_payload(survey, i + j)):
                        raise CommandError("Unexpected duplicate demo submission.")
                    submitted = sent + timedelta(days=j + 1)
                    SurveyRecipient.objects.filter(pk=recipient.pk).update(opened_at=submitted - timedelta(minutes=5), completed_at=submitted)
                    SurveyResponse.objects.filter(pk=response.pk).update(started_at=submitted - timedelta(minutes=5), submitted_at=submitted)
                    SurveyAnswer.objects.filter(response=response).update(created_at=submitted)
            if status == "CLOSED":
                Survey.objects.filter(pk=survey.pk).update(status=status, end_at=now - timedelta(days=1))
            # Invitations/submissions are historical: creation must precede them.
            Survey.objects.filter(pk=survey.pk).update(created_at=now - timedelta(days=21))
        validate_demo_surveys()
        self.stdout.write(self.style.SUCCESS(
            "Demo ready: 2 ADMIN + 3 MANAGER + 15 CUSTOMER; 20 feedbacks; 18 surveys; 61 submitted responses. "
            "Existing non-demo rows preserved. Use a fresh database for exact global totals."))
