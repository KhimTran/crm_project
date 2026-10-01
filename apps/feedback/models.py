from django.conf import settings
from django.db import models


class Feedback(models.Model):
    feedback_id = models.AutoField(primary_key=True)
    customer = models.ForeignKey("customers.Customer", on_delete=models.PROTECT, db_column="customer_id")
    product = models.ForeignKey("catalog.Product", on_delete=models.PROTECT, db_column="product_id")
    rating = models.PositiveSmallIntegerField()
    content = models.TextField()
    status = models.CharField(max_length=20)
    manager_note = models.TextField(null=True, blank=True)
    handled_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, db_column="handled_by", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "feedbacks"
        indexes = [
            models.Index(fields=["customer"], name="idx_feedbacks_customer"),
            models.Index(fields=["product"], name="idx_feedbacks_product"),
            models.Index(fields=["status"], name="idx_feedbacks_status"),
            models.Index(fields=["handled_by"], name="idx_feedbacks_handled_by"),
            models.Index(fields=["created_at"], name="idx_feedbacks_created_at"),
        ]
        constraints = [models.CheckConstraint(condition=models.Q(rating__gte=1, rating__lte=5), name="chk_feedbacks_rating")]
