from apps.accounts.testing import PortalTestCase as TestCase
from django.core.paginator import Paginator


from apps.accounts.models import Account
from apps.accounts.selectors import list_account_page
from apps.catalog.models import Brand, Category, Product
from apps.catalog.selectors import list_brand_page, list_category_page
from apps.customers.selectors import customer_queryset, filter_customers
from apps.feedback.models import Feedback
from apps.feedback.selectors import feedback_queryset, filter_feedbacks


class ListOrderingTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = Account.objects.create_superuser('ordering-admin@test.local', 'StrongPass!2026')
        customers = []
        for pk in [20, 3, 7]:
            customers.append(Account.objects.create_user(f'ordering-{pk}@test.local', 'StrongPass!2026', account_id=pk, full_name=f'Ordering {pk}'))
        for pk, name in [(17, 'AAA'), (2, 'ZZZ'), (9, 'MMM')]:
            Brand.objects.create(brand_id=pk, brand_name=name)
            Category.objects.create(category_id=pk, category_name=name)
        product = Product.objects.create(product_name='Ordering racket', price=100, brand_id=2, category_id=2)
        for pk, customer in zip([15, 2, 8], customers):
            Feedback.objects.create(feedback_id=pk, customer=customer, product=product, rating=5, content='Ordering feedback', status='NEW')

    def test_accounts_filtered_pages_are_numeric_ascending(self):
        ids = []
        for page in [1, 2]:
            ids.extend(row['account_id'] for row in list_account_page(self.admin, q='ordering-', role='CUSTOMER', page=page, page_size=2))
        self.assertEqual(ids, [3, 7, 20])

    def test_customers_preserve_order_after_search_and_pagination(self):
        query = filter_customers(customer_queryset(), {'q': 'Ordering'})
        pages = Paginator(query, 2)
        self.assertEqual([row.pk for page in pages for row in page], [3, 7, 20])

    def test_catalog_defaults_and_manual_sort(self):
        for selector in [list_brand_page, list_category_page]:
            self.assertEqual([row.pk for row in selector(page_size=2)], [2, 9])
            self.assertEqual([row.pk for row in selector(page=2, page_size=2)], [17])
            self.assertEqual([row.pk for row in selector(status='ACTIVE', q='M')], [9])
            self.assertEqual([row.pk for row in selector(sort='id', direction='desc')], [17, 9, 2])
            self.assertEqual([row.pk for row in selector(sort='name', direction='asc')], [17, 9, 2])
            self.assertEqual([row.pk for row in selector(sort='invalid', direction='desc')], [2, 9, 17])

    def test_feedback_filters_and_pages_preserve_numeric_order(self):
        query = filter_feedbacks(feedback_queryset(), {'status': 'NEW', 'q': 'Ordering', 'rating': 5})
        pages = Paginator(query, 2)
        self.assertEqual([row.pk for page in pages for row in page], [2, 8, 15])
