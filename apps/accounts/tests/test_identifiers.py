from django.apps import apps
from django.db import connection, models
from django.test import TestCase


BUSINESS_TABLES = {
    "accounts", "customers", "categories", "brands", "suppliers", "products",
    "customer_preferences", "feedbacks", "surveys", "survey_questions",
    "survey_options", "survey_recipients", "survey_responses", "survey_answers",
}


class IdentifierTypeTests(TestCase):
    def test_business_models_use_autofield(self):
        for model in apps.get_models():
            if model._meta.db_table in BUSINESS_TABLES:
                with self.subTest(model=model.__name__):
                    self.assertIsInstance(model._meta.pk, models.AutoField)
                    self.assertNotIsInstance(model._meta.pk, models.BigAutoField)
                    with connection.cursor() as cursor:
                        cursor.execute(
                            "SELECT COLUMN_TYPE, EXTRA FROM information_schema.COLUMNS "
                            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s AND COLUMN_NAME = %s",
                            [model._meta.db_table, model._meta.pk.column],
                        )
                        column_type, extra = cursor.fetchone()
                    self.assertEqual(column_type, "int")
                    self.assertIn("auto_increment", extra)

    def test_physical_business_ids_and_referencing_fks_are_int(self):
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT TABLE_NAME, COLUMN_NAME FROM information_schema.COLUMNS "
                "WHERE TABLE_SCHEMA = DATABASE() AND DATA_TYPE = 'bigint'"
            )
            self.assertEqual(cursor.fetchall(), ())
            cursor.execute(
                "SELECT TABLE_NAME, COLUMN_NAME, COLUMN_TYPE FROM information_schema.COLUMNS "
                "WHERE TABLE_SCHEMA = DATABASE()"
            )
            columns = {(table, column): column_type for table, column, column_type in cursor.fetchall()}
            cursor.execute(
                "SELECT TABLE_NAME, COLUMN_NAME, REFERENCED_TABLE_NAME "
                "FROM information_schema.KEY_COLUMN_USAGE "
                "WHERE TABLE_SCHEMA = DATABASE() AND REFERENCED_TABLE_NAME IS NOT NULL"
            )
            foreign_keys = cursor.fetchall()
            cursor.execute(
                "SELECT TABLE_NAME, CONSTRAINT_NAME FROM information_schema.TABLE_CONSTRAINTS "
                "WHERE TABLE_SCHEMA = DATABASE()"
            )
            constraints = set(cursor.fetchall())
            cursor.execute(
                "SELECT TABLE_NAME, INDEX_NAME FROM information_schema.STATISTICS "
                "WHERE TABLE_SCHEMA = DATABASE()"
            )
            indexes = set(cursor.fetchall())
        for (table, column), column_type in columns.items():
            if table in BUSINESS_TABLES and (column == "id" or column.endswith("_id") or column in ("created_by", "handled_by")):
                with self.subTest(table=table, column=column):
                    self.assertEqual(column_type, "int")
        for table, column, target in foreign_keys:
            if target in BUSINESS_TABLES:
                with self.subTest(fk=f"{table}.{column}"):
                    self.assertEqual(columns[(table, column)], "int")
        for table, name in (
            ("suppliers", "uq_suppliers_code"),
            ("survey_recipients", "uq_survey_recipients_survey_customer"),
            ("survey_responses", "uq_survey_responses_recipient"),
        ):
            self.assertIn((table, name), constraints)
        self.assertIn(("products", "idx_products_supplier"), indexes)
