"""Read-only verification of a migrated CRM MySQL database."""

import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django  # noqa: E402

django.setup()
from django.db import connection  # noqa: E402


PRIMARY_KEYS = {
    "accounts": "account_id", "customers": "customer_id",
    "categories": "category_id", "brands": "brand_id",
    "suppliers": "supplier_id", "products": "product_id",
    "customer_preferences": "preference_id", "feedbacks": "feedback_id",
    "surveys": "survey_id", "survey_questions": "question_id",
    "survey_options": "option_id", "survey_recipients": "recipient_id",
    "survey_responses": "response_id", "survey_answers": "answer_id",
}
FOREIGN_KEYS = {
    ("customers", "account_id"): ("accounts", "account_id"),
    ("products", "category_id"): ("categories", "category_id"),
    ("products", "brand_id"): ("brands", "brand_id"),
    ("products", "supplier_id"): ("suppliers", "supplier_id"),
    ("customer_preferences", "customer_id"): ("customers", "customer_id"),
    ("feedbacks", "customer_id"): ("customers", "customer_id"),
    ("feedbacks", "product_id"): ("products", "product_id"),
    ("feedbacks", "handled_by"): ("accounts", "account_id"),
    ("surveys", "created_by"): ("accounts", "account_id"),
    ("survey_questions", "survey_id"): ("surveys", "survey_id"),
    ("survey_options", "question_id"): ("survey_questions", "question_id"),
    ("survey_recipients", "survey_id"): ("surveys", "survey_id"),
    ("survey_recipients", "customer_id"): ("customers", "customer_id"),
    ("survey_responses", "recipient_id"): ("survey_recipients", "recipient_id"),
    ("survey_answers", "response_id"): ("survey_responses", "response_id"),
    ("survey_answers", "question_id"): ("survey_questions", "question_id"),
    ("survey_answers", "option_id"): ("survey_options", "option_id"),
}
TECHNICAL_TABLES = {
    "django_migrations", "django_session", "accounts_groups",
    "accounts_user_permissions", "auth_group", "auth_permission",
    "auth_group_permissions", "django_content_type", "django_admin_log",
}
FOREIGN_KEY_RULES = {
    ("customers", "account_id"): ("fk_customers_account", "CASCADE", "RESTRICT"),
    ("products", "category_id"): ("fk_products_category", "CASCADE", "RESTRICT"),
    ("products", "brand_id"): ("fk_products_brand", "CASCADE", "RESTRICT"),
    ("products", "supplier_id"): ("fk_products_supplier", "CASCADE", "RESTRICT"),
    ("customer_preferences", "customer_id"): ("fk_customer_preferences_customer", "CASCADE", "CASCADE"),
    ("feedbacks", "customer_id"): ("fk_feedbacks_customer", "CASCADE", "RESTRICT"),
    ("feedbacks", "product_id"): ("fk_feedbacks_product", "CASCADE", "RESTRICT"),
    ("feedbacks", "handled_by"): ("fk_feedbacks_handled_by", "CASCADE", "SET NULL"),
    ("surveys", "created_by"): ("fk_surveys_created_by", "CASCADE", "RESTRICT"),
    ("survey_questions", "survey_id"): ("fk_survey_questions_survey", "CASCADE", "CASCADE"),
    ("survey_options", "question_id"): ("fk_survey_options_question", "CASCADE", "CASCADE"),
    ("survey_recipients", "survey_id"): ("fk_survey_recipients_survey", "CASCADE", "CASCADE"),
    ("survey_recipients", "customer_id"): ("fk_survey_recipients_customer", "CASCADE", "RESTRICT"),
    ("survey_responses", "recipient_id"): ("fk_survey_responses_recipient", "CASCADE", "CASCADE"),
    ("survey_answers", "response_id"): ("fk_survey_answers_response", "CASCADE", "CASCADE"),
    ("survey_answers", "question_id"): ("fk_survey_answers_question", "CASCADE", "CASCADE"),
    ("survey_answers", "option_id"): ("fk_survey_answers_option", "CASCADE", "SET NULL"),
}
UNIQUE_KEYS = {
    ("accounts", "uq_accounts_email"): ("email",),
    ("customers", "uq_customers_account_id"): ("account_id",),
    ("suppliers", "uq_suppliers_code"): ("supplier_code",),
    ("survey_recipients", "uq_survey_recipients_survey_customer"): ("survey_id", "customer_id"),
    ("survey_responses", "uq_survey_responses_recipient"): ("recipient_id",),
}
REQUIRED_INDEXES = {
    ("customers", "idx_customers_full_name"), ("customers", "idx_customers_phone"),
    ("customers", "idx_customers_status"),
    ("categories", "idx_categories_name"), ("categories", "idx_categories_status"),
    ("brands", "idx_brands_name"), ("brands", "idx_brands_status"),
    ("suppliers", "idx_suppliers_name"), ("suppliers", "idx_suppliers_status"),
    ("products", "idx_products_category"), ("products", "idx_products_brand"),
    ("products", "idx_products_supplier"), ("products", "idx_products_name"),
    ("products", "idx_products_status"), ("products", "idx_products_price"),
    ("customer_preferences", "idx_customer_preferences_customer"),
    ("customer_preferences", "idx_customer_preferences_type"),
    ("feedbacks", "idx_feedbacks_customer"), ("feedbacks", "idx_feedbacks_product"),
    ("feedbacks", "idx_feedbacks_status"), ("feedbacks", "idx_feedbacks_handled_by"),
    ("feedbacks", "idx_feedbacks_created_at"),
    ("surveys", "idx_surveys_status"), ("surveys", "idx_surveys_created_by"),
    ("surveys", "idx_surveys_start_at"), ("surveys", "idx_surveys_end_at"),
    ("survey_questions", "idx_survey_questions_survey"),
    ("survey_questions", "idx_survey_questions_type"),
    ("survey_questions", "idx_survey_questions_sort"),
    ("survey_options", "idx_survey_options_question"),
    ("survey_options", "idx_survey_options_sort"),
    ("survey_recipients", "idx_survey_recipients_survey"),
    ("survey_recipients", "idx_survey_recipients_customer"),
    ("survey_recipients", "idx_survey_recipients_status"),
    ("survey_responses", "idx_survey_responses_status"),
    ("survey_answers", "idx_survey_answers_response"),
    ("survey_answers", "idx_survey_answers_question"),
    ("survey_answers", "idx_survey_answers_option"),
}
CHECKS = {
    ("accounts", "chk_accounts_role"), ("accounts", "chk_accounts_status"),
    ("customers", "chk_customers_status"),
    ("categories", "chk_categories_status"), ("brands", "chk_brands_status"),
    ("suppliers", "chk_suppliers_status"),
    ("products", "chk_products_price"), ("products", "chk_products_status"),
    ("feedbacks", "chk_feedbacks_rating"),
    ("survey_questions", "chk_survey_questions_sort_order"),
    ("survey_options", "chk_survey_options_sort_order"),
    ("survey_answers", "chk_survey_answers_rating"),
}


def main():
    issues = []
    with connection.cursor() as cursor:
        cursor.execute("SELECT DATABASE()")
        database = cursor.fetchone()[0]
        cursor.execute(
            "SELECT TABLE_NAME, COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_KEY, EXTRA "
            "FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = DATABASE()"
        )
        columns = {(table, column): (kind, nullable, key, extra)
                   for table, column, kind, nullable, key, extra in cursor.fetchall()}
        tables = {table for table, _ in columns}
        for table, pk in PRIMARY_KEYS.items():
            actual = columns.get((table, pk))
            if actual is None or actual[0] != "int" or actual[2] != "PRI" or "auto_increment" not in actual[3]:
                issues.append(f"PK {table}.{pk}: {actual}")
        missing_technical = sorted(TECHNICAL_TABLES - tables)
        if missing_technical:
            issues.append(f"Missing technical tables: {missing_technical}")
        cursor.execute(
            "SELECT k.TABLE_NAME, k.COLUMN_NAME, k.REFERENCED_TABLE_NAME, "
            "k.REFERENCED_COLUMN_NAME, k.CONSTRAINT_NAME, r.UPDATE_RULE, r.DELETE_RULE "
            "FROM information_schema.KEY_COLUMN_USAGE k "
            "JOIN information_schema.REFERENTIAL_CONSTRAINTS r "
            "ON r.CONSTRAINT_SCHEMA = k.CONSTRAINT_SCHEMA AND r.TABLE_NAME = k.TABLE_NAME "
            "AND r.CONSTRAINT_NAME = k.CONSTRAINT_NAME "
            "WHERE k.TABLE_SCHEMA = DATABASE() AND k.REFERENCED_TABLE_NAME IS NOT NULL"
        )
        fks = {(table, column): (target, target_column, name, update, delete)
               for table, column, target, target_column, name, update, delete in cursor.fetchall()}
        for source, target in FOREIGN_KEYS.items():
            actual = fks.get(source)
            if actual is None or actual[:2] != target or columns.get(source, (None,))[0] != "int":
                issues.append(f"FK {source}: {actual}")
            elif actual[2:] != FOREIGN_KEY_RULES[source]:
                issues.append(f"FK rules {source}: {actual[2:]}")
        cursor.execute(
            "SELECT TABLE_NAME, CONSTRAINT_NAME FROM information_schema.TABLE_CONSTRAINTS "
            "WHERE CONSTRAINT_SCHEMA = DATABASE() AND CONSTRAINT_TYPE = 'CHECK'"
        )
        checks = set(cursor.fetchall())
        for key in CHECKS - checks:
            issues.append(f"Missing CHECK {key}")
        cursor.execute(
            "SELECT TABLE_NAME, INDEX_NAME, NON_UNIQUE, COLUMN_NAME, SEQ_IN_INDEX "
            "FROM information_schema.STATISTICS WHERE TABLE_SCHEMA = DATABASE()"
        )
        indexes = {}
        for table, name, non_unique, column, position in cursor.fetchall():
            indexes.setdefault((table, name), []).append((position, column, non_unique))
        for key, expected in UNIQUE_KEYS.items():
            actual = indexes.get(key, [])
            if tuple(column for _, column, _ in sorted(actual)) != expected or any(row[2] for row in actual):
                issues.append(f"UNIQUE {key}: {actual}")
        for key in REQUIRED_INDEXES:
            if key not in indexes:
                issues.append(f"Missing index {key}")
        if ("survey_responses", "uq_survey_responses_recipient") not in indexes:
            issues.append("Missing unique index on response recipient")
        big = sorted((table, column, kind) for (table, column), (kind, _, _, _) in columns.items()
                     if kind.lower().startswith("bigint"))
        if big:
            issues.append(f"BIGINT columns remain: {big}")
        row_counts = {}
        for table in PRIMARY_KEYS:
            if table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM `{table}`")
                row_counts[table] = cursor.fetchone()[0]
        migrations = []
        if "django_migrations" in tables:
            cursor.execute("SELECT app, name FROM django_migrations ORDER BY app, name")
            migrations = cursor.fetchall()
    print(f"DATABASE={database} BUSINESS_TABLES={len(set(PRIMARY_KEYS) & tables)} "
          f"TECHNICAL_TABLES={len(TECHNICAL_TABLES & tables)} MIGRATIONS={len(migrations)}")
    print("ROWS=" + ", ".join(f"{table}:{row_counts[table]}" for table in sorted(row_counts)))
    for issue in issues:
        print("FAIL", issue)
    if issues:
        raise SystemExit(1)
    print("SCHEMA PASS: 14 INT PKs, 17 INT FKs, supplier FK, survey UNIQUE, indexes, technical tables")


if __name__ == "__main__":
    main()
