import os
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def send_otp_sms(phone_number, otp):
    """
    Dispatches a 6-digit OTP SMS to the recipient's phone number using Twilio.
    
    Security Guarantee:
    - API credentials are read strictly from settings / environment variables.
    - Never exposes OTP in frontend or client-side responses.
    - If Twilio is not configured, logs to server console and returns
      provider_configured=False so views can honestly inform the user.
    
    Returns:
        tuple: (success: bool, message: str, provider_configured: bool)
    """
    account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', '') or os.environ.get('TWILIO_ACCOUNT_SID', '')
    auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', '') or os.environ.get('TWILIO_AUTH_TOKEN', '')
    twilio_number = getattr(settings, 'TWILIO_PHONE_NUMBER', '') or os.environ.get('TWILIO_PHONE_NUMBER', '')

    clean_phone = str(phone_number).strip()

    if not (account_sid and auth_token and twilio_number):
        # Provider is not configured in environment
        logger.warning(
            f"[SMS SERVICE NOT CONFIGURED] Twilio credentials missing in environment. "
            f"Carrier SMS not sent to '{clean_phone}'. Development OTP: {otp}"
        )
        print("\n" + "=" * 65)
        print(" [FARMCONNECT AUTH SECURITY: DEVELOPMENT CONSOLE OTP LOG]")
        print(f" Recipient Phone : {clean_phone}")
        print(f" 6-Digit OTP Code: {otp}")
        print(" Status          : Twilio credentials not set in .env")
        print(" Note            : Real carrier SMS was NOT dispatched.")
        print("=" * 65 + "\n")
        return False, "SMS provider (Twilio) is not configured in environment variables.", False

    try:
        from twilio.rest import Client
        client = Client(account_sid, auth_token)

        # Standardize international format (E.164)
        formatted_phone = clean_phone
        if not formatted_phone.startswith('+'):
            if len(formatted_phone) == 10:
                formatted_phone = f"+91{formatted_phone}"
            else:
                formatted_phone = f"+{formatted_phone}"

        sms_body = (
            f"Your FarmConnect verification code is: {otp}. "
            f"Valid for 5 minutes. Do not share this OTP with anyone."
        )

        message = client.messages.create(
            body=sms_body,
            from_=twilio_number,
            to=formatted_phone
        )
        logger.info(f"[SMS SERVICE] OTP sent successfully to {formatted_phone}, SID: {message.sid}")
        return True, f"OTP has been dispatched via SMS to {formatted_phone}.", True

    except Exception as exc:
        logger.error(f"[SMS SERVICE ERROR] Failed to send SMS to {clean_phone}: {exc}")
        return False, f"SMS delivery failed: {str(exc)}", True
