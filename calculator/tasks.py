# backend/calculator/tasks.py
from celery import shared_task
from .models import CalculationResult, MpesaTransaction
from .utils.pdf_generator import create_pdf  # use create_pdf(filename) from pdf_generator
import logging
import os
from django.utils import timezone
from .models import CalculationResult

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_mpesa_callback(self, checkout_id, result_code, metadata):
    """Async: Process M-Pesa callback"""
    try:
        if int(result_code) == 0:
            receipt = next((x["Value"] for x in metadata if x["Name"] == "MpesaReceiptNumber"), None)
            amount = next((x["Value"] for x in metadata if x["Name"] == "Amount"), None)

            tx = MpesaTransaction.objects.filter(checkout_request_id=checkout_id).first()
            if tx and tx.calculation:
                tx.status = "Success"
                tx.mpesa_receipt_number = receipt
                tx.amount_paid = amount
                tx.save()

                calc = tx.calculation
                calc.paid = True
                calc.save()

                # Generate PDF in background (Celery worker will create and attach a PDF)
                generate_pdf_task.delay(calc.id)

                logger.info(f"Payment confirmed: {checkout_id}")
        else:
            MpesaTransaction.objects.filter(checkout_request_id=checkout_id).update(status="Failed")
    except Exception as exc:
        logger.error(f"Callback failed: {exc}")
        raise self.retry(exc=exc)


@shared_task
def generate_pdf_task(calc_id):
    """Generate PDF for paid calculation"""
    try:
        calc = CalculationResult.objects.get(id=calc_id, paid=True)
        pdf_dir = "media/pdfs"
        os.makedirs(pdf_dir, exist_ok=True)
        pdf_path = f"{pdf_dir}/quotation_{calc_id}.pdf"

        # Build a payload matching the PDF generator's expected shape
        payload = {
            "product": calc.product,
            "input": calc.input_data or {},
            "results": calc.result_data or {},
            "customerName": (calc.input_data or {}).get("customerName") if isinstance(calc.input_data, dict) else None,
        }

        # Create PDF file on disk
        create_pdf(payload, filename=pdf_path)

        # Attach relative path to the model's FileField (relative to MEDIA_ROOT)
        calc.pdf_file = f"pdfs/quotation_{calc_id}.pdf"
        calc.save()
    except Exception as e:
        logger.error(f"PDF generation failed: {e}")









@shared_task
def cleanup_expired_calculations():
    expired = CalculationResult.objects.filter(
        paid=False,
        expires_at__lt=timezone.now()
    )
    count = expired.count()
    expired.delete()
    print(f"Cleaned {count} expired calculations")