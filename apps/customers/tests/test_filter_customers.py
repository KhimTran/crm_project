from datetime import date

from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import Account
from apps.customers.selectors import age_group_of, customer_queryset, filter_customers, years_ago
from apps.customers.services import create_customer, delete_customer, lock_customer

PASSWORD = "CrmFixture!2026"

TODAY = date(2026, 10, 5)


# tv4: test bộ lọc filter_customers dùng chung cho TV5
class FilterCustomersTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.an = create_customer(password=PASSWORD, email="an@example.com", full_name="Nguyễn Văn An", phone="0900000001",
                                    date_of_birth=date(2008, 10, 5), gender="MALE", playing_level="BEGINNER",
                                    play_styles=["Tấn công"], brands=["Yonex", "Victor"])
        cls.binh = create_customer(password=PASSWORD, email="binh@example.com", full_name="Trần Thị Bình", phone="0900000002",
                                      date_of_birth=date(2008, 10, 6), gender="FEMALE",
                                      playing_level="COMPETITIVE", play_styles=["Phòng thủ"], brands=["Yonex"])
        cls.cuong = create_customer(password=PASSWORD, email="cuong@example.com", full_name="Lê Cường", phone="0900000003",
                                       date_of_birth=date(1960, 1, 1), gender="MALE", brands=["Li-Ning"])
        cls.dung = create_customer(password=PASSWORD, email="dung@example.com", full_name="Phạm Dũng", phone="0900000004")
        lock_customer(cls.cuong.pk)

    def ids(self, **params):
        return set(filter_customers(customer_queryset(), params, today=TODAY).values_list("pk", flat=True))

    def test_no_params_returns_all_non_deleted(self):
        self.assertEqual(self.ids(), {self.an.pk, self.binh.pk, self.cuong.pk, self.dung.pk})
        delete_customer(self.dung.pk)
        self.assertNotIn(self.dung.pk, self.ids())

    def test_age_group_boundary_on_birthday(self):
        # An tròn 18 đúng hôm nay, Bình mai mới 18.
        self.assertEqual(self.ids(age_group="18_24"), {self.an.pk})
        self.assertEqual(self.ids(age_group="UNDER_18"), {self.binh.pk})
        self.assertEqual(self.ids(age_group="55_PLUS"), {self.cuong.pk})
        self.assertEqual(self.ids(age_group="25_34"), set())

    def test_profile_and_preference_filters(self):
        self.assertEqual(self.ids(gender="MALE"), {self.an.pk, self.cuong.pk})
        self.assertEqual(self.ids(playing_level="COMPETITIVE"), {self.binh.pk})
        self.assertEqual(self.ids(play_style="Tấn công"), {self.an.pk})
        self.assertEqual(self.ids(brand="Yonex"), {self.an.pk, self.binh.pk})
        self.assertEqual(self.ids(account_status="LOCKED"), {self.cuong.pk})
        self.assertEqual(self.ids(q="bình"), {self.binh.pk})
        self.assertEqual(self.ids(q="0900000004"), {self.dung.pk})

    def test_filters_combine_without_duplicate_rows(self):
        self.assertEqual(self.ids(brand="Yonex", gender="FEMALE"), {self.binh.pk})
        qs = filter_customers(customer_queryset(), {"brand": "Yonex", "play_style": "Tấn công"}, today=TODAY)
        self.assertEqual(qs.count(), 1)

    def test_age_helpers(self):
        self.assertEqual(years_ago(date(2028, 2, 29), 1), date(2027, 2, 28))
        self.assertEqual(age_group_of(date(2008, 10, 5), TODAY), "18_24")
        self.assertEqual(age_group_of(date(2008, 10, 6), TODAY), "UNDER_18")
        self.assertIsNone(age_group_of(None, TODAY))


# tv4: test bộ lọc trên trang danh sách khách hàng
class CustomerListFilterViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.manager = Account.objects.create_user("manager@example.com", "Quanly@12345")
        cls.manager.groups.add(Group.objects.create(name="CRM_MANAGER"))
        create_customer(password=PASSWORD, email="an@example.com", full_name="Nguyễn Văn An", phone="0900000001",
                        playing_level="BEGINNER", brands=["Yonex"])
        create_customer(password=PASSWORD, email="binh@example.com", full_name="Trần Thị Bình", phone="0900000002",
                        brands=["Victor"])

    def test_filter_form_narrows_list_and_shows_labels(self):
        self.client.force_login(self.manager)
        response = self.client.get(reverse("customers:list"), {"playing_level": "BEGINNER"})
        self.assertContains(response, "Nguyễn Văn An")
        self.assertNotContains(response, "Trần Thị Bình")
        self.assertContains(response, "Mới chơi")

    def test_invalid_choice_does_not_filter(self):
        self.client.force_login(self.manager)
        response = self.client.get(reverse("customers:list"), {"age_group": "abc"})
        self.assertContains(response, "Nguyễn Văn An")
        self.assertContains(response, "Trần Thị Bình")
