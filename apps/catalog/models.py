from django.db import models


class Status(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    INACTIVE = "INACTIVE", "Inactive"


class Category(models.Model):
    category_id = models.AutoField(primary_key=True)
    category_name = models.CharField(max_length=100)
    description = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "categories"

    def __str__(self):
        return self.category_name


class Brand(models.Model):
    brand_id = models.AutoField(primary_key=True)
    brand_name = models.CharField(max_length=100)
    description = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "brands"

    def __str__(self):
        return self.brand_name


class Supplier(models.Model):
    supplier_id = models.AutoField(primary_key=True)
    supplier_code = models.CharField(max_length=30)
    supplier_name = models.CharField(max_length=150)
    address = models.CharField(max_length=255, null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "suppliers"
        indexes = [models.Index(fields=["supplier_name"], name="idx_suppliers_name"),
                   models.Index(fields=["status"], name="idx_suppliers_status")]
        constraints = [
            models.UniqueConstraint(fields=["supplier_code"], name="uq_suppliers_code"),
            models.CheckConstraint(condition=models.Q(status__in=Status.values), name="chk_suppliers_status"),
        ]

    def __str__(self):
        return self.supplier_name


class Product(models.Model):
    product_id = models.AutoField(primary_key=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, db_column="category_id")
    brand = models.ForeignKey(Brand, on_delete=models.PROTECT, db_column="brand_id")
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, db_column="supplier_id")
    product_name = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "products"
        indexes = [
            models.Index(fields=["category"], name="idx_products_category"),
            models.Index(fields=["brand"], name="idx_products_brand"),
            models.Index(fields=["supplier"], name="idx_products_supplier"),
        ]

    def __str__(self):
        return self.product_name
