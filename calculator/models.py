# backend/calculator/models.py
from django.db import models
from django.utils import timezone
from datetime import timedelta


class MpesaTransaction(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True)
    agent_name = models.CharField(max_length=100, blank=True, null=True)
    phone_number = models.CharField(max_length=20)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    calculation = models.ForeignKey(
        "CalculationResult",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="transactions",
    )
    status = models.CharField(max_length=50, default='Pending')
    merchant_request_id = models.CharField(max_length=100, blank=True, null=True)
    checkout_request_id = models.CharField(max_length=100, blank=True, null=True)
    mpesa_receipt_number = models.CharField(max_length=100, blank=True, null=True)
    transaction_date = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.phone_number} - {self.amount} ({self.status})"


class CalculationResult(models.Model):
    """Stores calculation inputs and results until the user pays to download them."""
    product = models.CharField(max_length=100)
    input_data = models.JSONField()
    result_data = models.JSONField()
    amount_due = models.DecimalField(max_digits=8, decimal_places=2, default=5.00)
    paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    pdf_file = models.FileField(upload_to='pdfs/', null=True, blank=True)

    # 60-SECOND EXPIRY — SET ON SAVE (NO LAMBDA!)
    expires_at = models.DateTimeField(default=timezone.now)

    def save(self, *args, **kwargs):
        if not self.pk:  # Only on creation
            self.expires_at = timezone.now() + timedelta(seconds=60)
        super().save(*args, **kwargs)

    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"Calc {self.id} for {self.product} (paid={self.paid})"