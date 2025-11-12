# backend/calculator/utils/mpesa.py
import os
import re
import base64
import requests
from datetime import datetime
from requests.auth import HTTPBasicAuth
from decouple import config
from django.conf import settings


# === MPESA CONFIG (LOADED FROM .env) ===
MPESA_BASE_URL = "https://sandbox.safaricom.co.ke"

CONSUMER_KEY = config('MPESA_CONSUMER_KEY')
CONSUMER_SECRET = config('MPESA_CONSUMER_SECRET')
BUSINESS_SHORTCODE = config('MPESA_SHORTCODE')
PASSKEY = config('MPESA_PASSKEY')
CALLBACK_URL = config('MPESA_CALLBACK_URL')


def get_access_token():
    """Fetch OAuth access token from Safaricom."""
    url = f"{MPESA_BASE_URL}/oauth/v1/generate?grant_type=client_credentials"
    response = requests.get(url, auth=HTTPBasicAuth(CONSUMER_KEY, CONSUMER_SECRET))
    response.raise_for_status()
    return response.json().get('access_token')


def _normalize_phone(pn: str) -> str:
    """Convert Kenyan phone number to 254XXXXXXXXX format."""
    if not pn:
        return pn
    s = re.sub(r"[^0-9]", "", str(pn))
    if s.startswith("0") and len(s) == 10:
        return "254" + s[1:]
    if s.startswith("7") and len(s) == 9:
        return "254" + s
    if s.startswith("254") and len(s) == 12:
        return s
    return s


def initiate_stk_push(phone_number, amount, account_reference="Kenindia Premiums Calculator"):
    """
    Initiate STK Push to user's phone.
    Phone should be in 254XXXXXXXXX format.
    """
    access_token = get_access_token()
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    password = base64.b64encode((BUSINESS_SHORTCODE + PASSKEY + timestamp).encode()).decode("utf-8")

    stk_url = f"{MPESA_BASE_URL}/mpesa/stkpush/v1/processrequest"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    pn = _normalize_phone(phone_number)
    try:
        amt = int(float(amount))
    except Exception:
        amt = 1  # Fallback

    payload = {
        "BusinessShortCode": BUSINESS_SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amt,
        "PartyA": pn,
        "PartyB": BUSINESS_SHORTCODE,
        "PhoneNumber": pn,
        "CallBackURL": CALLBACK_URL,
        "AccountReference": account_reference,
        "TransactionDesc": "Premium Payment",
    }

    response = requests.post(stk_url, json=payload, headers=headers)
    return response.json()


def parse_stk_callback(callback_data):
    """Parse M-Pesa STK Push callback and extract key fields."""
    result = callback_data.get("Body", {}).get("stkCallback", {})
    
    merchant_request_id = result.get("MerchantRequestID")
    checkout_request_id = result.get("CheckoutRequestID")
    result_code = result.get("ResultCode")
    result_desc = result.get("ResultDesc")

    mpesa_receipt_number = None
    transaction_date = None
    amount = None
    phone_number = None

    if result_code == 0:
        items = result.get("CallbackMetadata", {}).get("Item", [])
        for item in items:
            name = item.get("Name")
            value = item.get("Value")
            if name == "MpesaReceiptNumber":
                mpesa_receipt_number = value
            elif name == "TransactionDate":
                date_str = str(value)
                transaction_date = datetime.strptime(date_str, "%Y%m%d%H%M%S")
            elif name == "Amount":
                amount = value
            elif name == "PhoneNumber":
                phone_number = str(value)

    return {
        "merchant_request_id": merchant_request_id,
        "checkout_request_id": checkout_request_id,
        "result_code": result_code,
        "result_desc": result_desc,
        "mpesa_receipt_number": mpesa_receipt_number,
        "transaction_date": transaction_date,
        "amount": amount,
        "phone_number": phone_number,
    }