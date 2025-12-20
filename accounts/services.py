"""
سرویس‌های مربوط به OTP و ارسال پیامک با ملی پیامک
"""
import requests
import logging
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from .models import OTPVerification

logger = logging.getLogger(__name__)


class MeliPayamakService:
    """
    سرویس ارسال پیامک با API ملی پیامک
    """
    BASE_URL = "https://console.melipayamak.com/api/send/shared/"

    def __init__(self):
        self.username = settings.MELIPAYAMAK_USERNAME
        self.api_key = settings.MELIPAYAMAK_API_KEY
        self.sender_number = settings.MELIPAYAMAK_SENDER_NUMBER
        self.pattern_code = settings.MELIPAYAMAK_PATTERN_CODE

    def send_otp(self, phone_number, otp_code):
        """
        ارسال کد OTP به شماره تلفن از طریق پترن ملی پیامک

        Args:
            phone_number (str): شماره تلفن گیرنده
            otp_code (str): کد OTP

        Returns:
            bool: موفقیت یا عدم موفقیت ارسال
        """
        try:
            # کلید در انتهای URL اضافه می‌شه
            url = f"{self.BASE_URL}{self.pattern_code}/{self.api_key}"

            payload = {
                "bodyId": self.pattern_code,
                "to": phone_number,
                "args": [otp_code]
            }

            headers = {
                "Content-Type": "application/json"
            }

            response = requests.post(url, json=payload, headers=headers, timeout=10)

            if response.status_code == 200:
                logger.info(f"✓ OTP sent successfully to {phone_number}")
                return True
            else:
                logger.error(f"✗ Failed to send OTP to {phone_number}: {response.text}")
                return False

        except requests.exceptions.Timeout:
            logger.error(f"✗ Timeout while sending OTP to {phone_number}")
            return False
        except requests.exceptions.RequestException as e:
            logger.error(f"✗ Error sending OTP to {phone_number}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"✗ Unexpected error: {str(e)}")
            return False


class OTPService:
    """
    سرویس مدیریت OTP
    """

    @staticmethod
    def create_otp(phone_number, expiry_minutes=5):
        """
        ایجاد کد OTP جدید برای شماره تلفن

        Args:
            phone_number (str): شماره تلفن
            expiry_minutes (int): زمان انقضا به دقیقه

        Returns:
            OTPVerification: آبجکت OTP ایجاد شده
        """
        # حذف OTP های قبلی استفاده نشده
        OTPVerification.objects.filter(
            phone_number=phone_number,
            is_used=False
        ).update(is_used=True)

        # تولید کد جدید
        otp_code = OTPVerification.generate_otp()
        expires_at = timezone.now() + timedelta(minutes=expiry_minutes)

        # ذخیره در دیتابیس
        otp = OTPVerification.objects.create(
            phone_number=phone_number,
            otp_code=otp_code,
            expires_at=expires_at
        )

        # ارسال پیامک
        sms_service = MeliPayamakService()
        sms_sent = sms_service.send_otp(phone_number, otp_code)

        if not sms_sent:
            logger.warning(f"OTP created but SMS failed for {phone_number}")

        return otp

    @staticmethod
    def verify_otp(phone_number, otp_code):
        """
        تایید کد OTP

        Args:
            phone_number (str): شماره تلفن
            otp_code (str): کد OTP وارد شده

        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            otp = OTPVerification.objects.filter(
                phone_number=phone_number,
                otp_code=otp_code,
                is_used=False
            ).order_by('-created_at').first()

            if not otp:
                return False, "کد OTP نامعتبر است"

            # بررسی تعداد تلاش
            if otp.attempts >= 5:
                return False, "تعداد تلاش‌های شما به حداکثر رسیده است"

            # افزایش تعداد تلاش
            otp.attempts += 1
            otp.save()

            # بررسی انقضا
            if otp.is_expired():
                return False, "کد OTP منقضی شده است. لطفاً کد جدید درخواست کنید"

            # بررسی صحت کد
            if otp.otp_code == otp_code:
                otp.is_used = True
                otp.save()
                return True, "شماره تلفن با موفقیت تایید شد"
            else:
                return False, "کد OTP اشتباه است"

        except Exception as e:
            logger.error(f"Error verifying OTP: {str(e)}")
            return False, "خطایی در تایید کد رخ داد"

    @staticmethod
    def can_request_new_otp(phone_number, cooldown_seconds=120):
        """
        بررسی امکان درخواست OTP جدید (برای جلوگیری از spam)

        Args:
            phone_number (str): شماره تلفن
            cooldown_seconds (int): حداقل فاصله زمانی بین درخواست‌ها (ثانیه)

        Returns:
            tuple: (can_request: bool, remaining_seconds: int)
        """
        last_otp = OTPVerification.objects.filter(
            phone_number=phone_number
        ).order_by('-created_at').first()

        if not last_otp:
            return True, 0

        time_since_last = timezone.now() - last_otp.created_at
        cooldown_delta = timedelta(seconds=cooldown_seconds)

        if time_since_last < cooldown_delta:
            remaining = int((cooldown_delta - time_since_last).total_seconds())
            return False, remaining
        else:
            return True, 0
