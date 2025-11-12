# backend/calculator/views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from datetime import date, timedelta
from decimal import Decimal
from django.http import HttpResponse
from django.utils.dateparse import parse_datetime
from django.utils import timezone
import re

from .utils.calculations import (
    calculate_premium_logic,
    calculate_sum_assured_logic,
    calculate_premium_logic_academic_advantage,
    calculate_sum_assured_logic_academic_advantage,
    calculate_premium_logic_money_back_15,
    calculate_sum_assured_logic_money_back_15,
    calculate_premium_logic_money_back_10,
    calculate_sum_assured_logic_money_back_10,
)
from .models import MpesaTransaction, CalculationResult
from .utils.pdf_generator import render_pdf_to_bytes
from .tasks import process_mpesa_callback


# --------------------------------------------------------------------
# Utility Functions
# --------------------------------------------------------------------
def get_age_next_birthday(dob):
    """Compute actual age and age next birthday."""
    today = date.today()
    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    return age, age + 1


def _coerce_bool(val):
    """Safely convert checkbox-like values to boolean."""
    if isinstance(val, bool):
        return val
    if val is None:
        return False
    if isinstance(val, str):
        return val.lower() in ("1", "true", "yes", "y", "on")
    return bool(val)


def clean_phone_number(phone_number):
    """Normalize Kenyan phone numbers to 2547XXXXXXXX or 2541XXXXXXXX."""
    if not phone_number:
        return None
    phone = re.sub(r"[^\d]", "", str(phone_number))
    if (phone.startswith("07") or phone.startswith("01")) and len(phone) == 10:
        phone = "254" + phone[1:]
    elif phone.startswith("+254"):
        phone = phone[1:]
    elif phone.startswith("7") and len(phone) == 9:
        phone = "254" + phone
    elif phone.startswith("1") and len(phone) == 9:
        phone = "254" + phone
    elif (phone.startswith("2547") or phone.startswith("2541")) and len(phone) == 12:
        pass
    else:
        return None
    return phone if re.match(r"^254[17]\d{8}$", phone) else None


# --------------------------------------------------------------------
# Premium Calculation (SA → Premium)
# --------------------------------------------------------------------
@api_view(["POST"])
def calculate_premium(request):
    data = request.data
    product = data.get("product", "").lower()
    dob_str = data.get("dob")
    term = data.get("term")
    mode = data.get("mode", "yearly").lower()
    sum_assured = data.get("sumAssured")
    gender = data.get("gender", "male").lower()
    smoker = data.get("smoker", "non-smoker").lower()
    dab_included = _coerce_bool(data.get("dabIncluded", True))

    # Validation
    if not product or not dob_str or sum_assured in (None, ""):
        return Response({"error": "Missing required fields."}, status=400)
    if not term or not str(term).isdigit():
        return Response({"error": "Invalid term."}, status=400)

    try:
        dob = date.fromisoformat(dob_str)
        term = int(term)
        sum_assured = float(sum_assured)
    except ValueError:
        return Response({"error": "Invalid date or number."}, status=400)

    actual_age, age_next_birthday = get_age_next_birthday(dob)

    # Product rules
    if product == "money_back_15":
        if sum_assured < 50000:
            return Response({"error": "Min SA: KES 50,000"}, status=400)
        if not (18 <= actual_age <= 45):
            return Response({"error": "Age 18–45 required"}, status=400)
        term = 15
    elif product == "money_back_10":
        if sum_assured < 50000:
            return Response({"error": "Min SA: KES 50,000"}, status=400)
        if not (18 <= age_next_birthday <= 50):
            return Response({"error": "Age Next Birthday 18–50"}, status=400)
        term = 10
    elif product == "academic_advantage" and sum_assured < 100000:
        return Response({"error": "Min SA: KES 100,000"}, status=400)

    # Calculate
    try:
        if product == "education_endowment":
            result = calculate_premium_logic(product, term, mode, sum_assured, age_next_birthday, gender, smoker, dab_included)
        elif product == "academic_advantage":
            result = calculate_premium_logic_academic_advantage(product, term, mode, sum_assured, age_next_birthday, gender, smoker, dab_included)
        elif product == "money_back_15":
            result = calculate_premium_logic_money_back_15(product, term, mode, sum_assured, age_next_birthday, gender, smoker, dab_included)
        elif product == "money_back_10":
            result = calculate_premium_logic_money_back_10(product, term, mode, sum_assured, age_next_birthday, gender, smoker, dab_included)
        else:
            return Response({"error": "Unsupported product"}, status=400)

        amount_due = Decimal("5.00")
        calc = CalculationResult.objects.create(
            product=product,
            input_data={**data, "actualAge": actual_age, "ageNextBirthday": age_next_birthday},
            result_data=result,
            amount_due=amount_due,
            paid=False,
            
        )

        return Response({
            "message": "Pay to download",
            "calculation_id": calc.id,
            "amount_due": float(amount_due),
        })

    except Exception as e:
        return Response({"error": str(e)}, status=500)


# --------------------------------------------------------------------
# Sum Assured Calculation (Premium → SA)
# --------------------------------------------------------------------
@api_view(["POST"])
def calculate_sum_assured(request):
    # Same structure as above, just reversed
    data = request.data
    product = data.get("product", "").lower()
    dob_str = data.get("dob")
    term = data.get("term")
    mode = data.get("mode", "yearly").lower()
    premium = data.get("premium")
    gender = data.get("gender", "male").lower()
    smoker = data.get("smoker", "non-smoker").lower()
    dab_included = _coerce_bool(data.get("dabIncluded", True))

    if not product or not dob_str or premium in (None, ""):
        return Response({"error": "Missing fields."}, status=400)
    if not term or not str(term).isdigit():
        return Response({"error": "Invalid term."}, status=400)

    try:
        dob = date.fromisoformat(dob_str)
        term = int(term)
        premium = float(premium)
    except ValueError:
        return Response({"error": "Invalid input."}, status=400)

    actual_age, age_next_birthday = get_age_next_birthday(dob)

    if product == "money_back_15":
        if not (18 <= actual_age <= 45):
            return Response({"error": "Age 18–45"}, status=400)
        term = 15
    elif product == "money_back_10":
        if not (18 <= age_next_birthday <= 50):
            return Response({"error": "Age Next Birthday 18–50"}, status=400)
        term = 10

    try:
        if product == "education_endowment":
            result = calculate_sum_assured_logic(product, term, mode, premium, age_next_birthday, gender, smoker, dab_included)
        elif product == "academic_advantage":
            result = calculate_sum_assured_logic_academic_advantage(product, term, mode, premium, age_next_birthday, gender, smoker, dab_included)
        elif product == "money_back_15":
            result = calculate_sum_assured_logic_money_back_15(product, term, mode, premium, age_next_birthday, gender, smoker, dab_included)
        elif product == "money_back_10":
            result = calculate_sum_assured_logic_money_back_10(product, term, mode, premium, age_next_birthday, gender, smoker, dab_included)
        else:
            return Response({"error": "Unsupported product"}, status=400)

        amount_due = Decimal("5.00")
        calc = CalculationResult.objects.create(
            product=product,
            input_data={**data, "actualAge": actual_age, "ageNextBirthday": age_next_birthday},
            result_data=result,
            amount_due=amount_due,
            paid=False,
            


        )

        return Response({
            "message": "Pay to download",
            "calculation_id": calc.id,
            "amount_due": float(amount_due),
        })

    except Exception as e:
        return Response({"error": str(e)}, status=500)


# --------------------------------------------------------------------
# Payment & Download
# --------------------------------------------------------------------




@api_view(["GET"])
def check_calculation_status(request, calc_id):
    try:
        calc = CalculationResult.objects.get(pk=calc_id)
        
        # EXPIRE IF 60 SECONDS PASSED
        if calc.is_expired() and not calc.paid:
            calc.paid = False  # just in case
            return Response({
                "paid": False,
                "expired": True,
                "message": "Retry — you delayed paying."
            }, status=200)

        return Response({"paid": calc.paid, "expired": False})
    except CalculationResult.DoesNotExist:
        return Response({"error": "Not found"}, status=404)




@api_view(["GET"])
def download_result(request, calc_id):
    try:
        calc = CalculationResult.objects.get(pk=calc_id)
    except CalculationResult.DoesNotExist:
        return Response({"error": "Not found"}, status=404)

    if not calc.paid:
        return Response({"error": "Payment required"}, status=402)

    return Response({
        "calculation_id": calc.id,
        "product": calc.product,
        "input": calc.input_data,
        "results": calc.result_data,
        "pdf_url": calc.pdf_file.url if calc.pdf_file else None,
    })


@api_view(["POST"])
def generate_pdf_quotation(request):
    data = request.data
    calc = None
    if data.get("calculation_id"):
        try:
            calc = CalculationResult.objects.get(pk=int(data["calculation_id"]))
        except CalculationResult.DoesNotExist:
            return Response({"error": "Not found"}, status=404)

    payload = {
        "product": calc.product if calc else data.get("product"),
        "input": calc.input_data if calc else data.get("input", {}),
        "results": calc.result_data if calc else data.get("results", {}),
        "customerName": data.get("customerName"),
    }

    pdf_bytes = render_pdf_to_bytes(payload)
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="kenindia_quotation.pdf"'
    return response


# --------------------------------------------------------------------
# M-Pesa STK Push
# --------------------------------------------------------------------
@api_view(["POST"])
def stk_push_view(request):
    phone_number = request.data.get("phone_number")
    amount = request.data.get("amount")
    calculation_id = request.data.get("calculation_id")

    if not phone_number or not amount:
        return Response({"error": "Phone and amount required"}, status=400)

    phone_number = clean_phone_number(phone_number)
    if not phone_number:
        return Response({"error": "Invalid phone format"}, status=400)

    from .utils.mpesa import initiate_stk_push
    mpesa_response = initiate_stk_push(phone_number, amount)

    tx = MpesaTransaction.objects.create(
        phone_number=phone_number,
        amount=amount,
        status="Pending",
        merchant_request_id=mpesa_response.get("MerchantRequestID"),
        checkout_request_id=mpesa_response.get("CheckoutRequestID"),
    )

    if calculation_id:
        try:
            calc = CalculationResult.objects.get(pk=int(calculation_id))
            tx.calculation = calc
            tx.save()
        except CalculationResult.DoesNotExist:
            pass

    return Response(mpesa_response)


# --------------------------------------------------------------------
# M-Pesa Callback (Celery)
# --------------------------------------------------------------------
@api_view(["POST"])
def stk_callback_view(request):
    data = request.data
    callback = data.get("Body", {}).get("stkCallback", {})
    checkout_id = callback.get("CheckoutRequestID")
    result_code = callback.get("ResultCode", -1)
    metadata = callback.get("CallbackMetadata", {}).get("Item", [])

    process_mpesa_callback.delay(checkout_id, result_code, metadata)

    return Response({"ResultCode": 0, "ResultDesc": "Accepted"})