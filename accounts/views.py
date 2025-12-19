"""
Views برای احراز هویت و مدیریت پروفایل
"""
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.conf import settings
import logging

from .forms import (
    SignupForm, LoginForm, OTPVerifyForm,
    ProfileEditForm, ChangePasswordForm
)
from .models import User, OTPVerification, LoginAttempt
from .services import OTPService

logger = logging.getLogger('accounts')


def get_client_ip(request):
    """دریافت IP کاربر"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def log_login_attempt(request, username, success=False):
    """ثبت تلاش ورود"""
    try:
        LoginAttempt.objects.create(
            username=username,
            ip_address=get_client_ip(request),
            success=success,
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
        )
    except Exception as e:
        logger.error(f"Failed to log login attempt: {str(e)}")


@require_http_methods(["GET", "POST"])
def signup_view(request):
    """
    صفحه ثبت‌نام کاربر جدید
    """
    if request.user.is_authenticated:
        return redirect('index')

    if request.method == 'POST':
        form = SignupForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # ایجاد کاربر مستقیماً (بدون OTP - موقتاً)
                user = User.objects.create_user(
                    username=form.cleaned_data['username'],
                    email=form.cleaned_data['email'],
                    password=form.cleaned_data['password1'],
                    first_name=form.cleaned_data['first_name'],
                    last_name=form.cleaned_data['last_name'],
                    phone_number=form.cleaned_data['phone_number'],
                    is_phone_verified=True  # موقتاً True
                )

                # ذخیره عکس پروفایل
                if form.cleaned_data.get('profile_picture'):
                    user.profile_picture = form.cleaned_data['profile_picture']
                    user.save()

                # ورود خودکار
                login(request, user)

                logger.info(f"User {user.username} registered successfully (without OTP)")
                messages.success(request, 'ثبت‌نام با موفقیت انجام شد!')
                return redirect('index')

            except Exception as e:
                logger.error(f"Error creating user: {str(e)}")
                messages.error(request, f'خطا در ایجاد حساب کاربری: {str(e)}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{error}')
    else:
        form = SignupForm()

    context = {
        'form': form,
        'recaptcha_site_key': settings.RECAPTCHA_SITE_KEY
    }
    return render(request, 'authentication/signup.html', context)


@require_http_methods(["GET", "POST"])
def verify_otp_view(request):
    """
    صفحه تایید کد OTP
    """
    if 'otp_phone' not in request.session:
        messages.error(request, 'ابتدا باید ثبت‌نام کنید')
        return redirect('signup')

    phone_number = request.session['otp_phone']

    if request.method == 'POST':
        form = OTPVerifyForm(request.POST)
        if form.is_valid():
            otp_code = form.cleaned_data['otp_code']

            # تایید OTP
            success, message = OTPService.verify_otp(phone_number, otp_code)

            if success:
                # ایجاد کاربر
                signup_data = request.session.get('signup_data')
                if not signup_data:
                    messages.error(request, 'اطلاعات ثبت‌نام یافت نشد. لطفاً دوباره تلاش کنید')
                    return redirect('signup')

                try:
                    user = User.objects.create_user(
                        username=signup_data['username'],
                        email=signup_data['email'],
                        password=signup_data['password'],
                        first_name=signup_data['first_name'],
                        last_name=signup_data['last_name'],
                        phone_number=signup_data['phone_number'],
                        is_phone_verified=True
                    )

                    # ورود خودکار
                    login(request, user)

                    # پاک کردن session
                    del request.session['otp_phone']
                    del request.session['signup_data']

                    logger.info(f"User {user.username} registered successfully")
                    messages.success(request, 'ثبت‌نام با موفقیت انجام شد!')
                    return redirect('index')

                except Exception as e:
                    logger.error(f"Error creating user: {str(e)}")
                    messages.error(request, 'خطا در ایجاد حساب کاربری')
            else:
                messages.error(request, message)
    else:
        form = OTPVerifyForm()

    context = {
        'form': form,
        'phone_number': phone_number
    }
    return render(request, 'authentication/verify_otp.html', context)


@require_http_methods(["POST"])
def resend_otp_view(request):
    """
    ارسال مجدد کد OTP
    """
    if 'otp_phone' not in request.session:
        return JsonResponse({'success': False, 'message': 'شماره تلفن یافت نشد'})

    phone_number = request.session['otp_phone']

    # بررسی cooldown
    can_request, remaining = OTPService.can_request_new_otp(phone_number)
    if not can_request:
        return JsonResponse({
            'success': False,
            'message': f'لطفاً {remaining} ثانیه صبر کنید'
        })

    # ارسال OTP جدید
    OTPService.create_otp(phone_number)
    logger.info(f"OTP resent to {phone_number}")

    return JsonResponse({
        'success': True,
        'message': 'کد تایید جدید ارسال شد'
    })


@require_http_methods(["GET", "POST"])
def signin_view(request):
    """
    صفحه ورود کاربر
    """
    if request.user.is_authenticated:
        return redirect('index')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        username_or_email = request.POST.get('username', '')

        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')

            # سعی برای ورود با username
            user = authenticate(request, username=username, password=password)

            # اگه نشد، سعی با email
            if user is None:
                try:
                    user_obj = User.objects.get(email=username)
                    user = authenticate(request, username=user_obj.username, password=password)
                except User.DoesNotExist:
                    user = None

            if user is not None:
                login(request, user)
                log_login_attempt(request, username_or_email, success=True)
                logger.info(f"User {user.username} logged in successfully")

                next_url = request.GET.get('next', 'index')
                return redirect(next_url)
            else:
                log_login_attempt(request, username_or_email, success=False)
                messages.error(request, 'نام کاربری/ایمیل یا رمز عبور اشتباه است')
        else:
            log_login_attempt(request, username_or_email, success=False)
            for error in form.non_field_errors():
                messages.error(request, error)
    else:
        form = LoginForm()

    context = {
        'form': form,
        'recaptcha_site_key': settings.RECAPTCHA_SITE_KEY
    }
    return render(request, 'authentication/signin.html', context)


@login_required
def signout_view(request):
    """
    خروج کاربر
    """
    username = request.user.username
    logout(request)
    logger.info(f"User {username} logged out")
    messages.success(request, 'با موفقیت خارج شدید')
    return redirect('signin')


@login_required
@require_http_methods(["GET", "POST"])
def profile_edit_view(request):
    """
    ویرایش پروفایل کاربر
    """
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES, instance=request.user, user=request.user)
        if form.is_valid():
            form.save()
            logger.info(f"User {request.user.username} updated profile")
            messages.success(request, 'پروفایل با موفقیت به‌روزرسانی شد')
            return redirect('profile_edit')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    else:
        form = ProfileEditForm(instance=request.user, user=request.user)

    context = {
        'form': form,
        'user': request.user
    }
    return render(request, 'authentication/profile_edit.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def change_password_view(request):
    """
    تغییر رمز عبور
    """
    if request.method == 'POST':
        form = ChangePasswordForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            # به‌روزرسانی session برای جلوگیری از logout
            update_session_auth_hash(request, request.user)
            logger.info(f"User {request.user.username} changed password")
            messages.success(request, 'رمز عبور با موفقیت تغییر کرد')
            return redirect('profile_edit')
        else:
            for error in form.non_field_errors():
                messages.error(request, error)
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    else:
        form = ChangePasswordForm(request.user)

    context = {'form': form}
    return render(request, 'authentication/change_password.html', context)


def forgot_password_view(request):
    """
    بازیابی رمز عبور (برای آینده)
    """
    # TODO: پیاده‌سازی بازیابی رمز با OTP یا ایمیل
    return render(request, 'authentication/forgotPassword.html')
