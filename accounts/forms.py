"""
فرم‌های احراز هویت و مدیریت پروفایل
"""
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from django.conf import settings
import requests
from .models import User


class ReCAPTCHAMixin:
    """
    Mixin برای اضافه کردن reCAPTCHA به فرم‌ها
    """
    def verify_recaptcha(self, token):
        """
        تایید reCAPTCHA با Google API
        """
        if not token:
            return False

        try:
            response = requests.post(
                settings.RECAPTCHA_VERIFY_URL,
                data={
                    'secret': settings.RECAPTCHA_SECRET_KEY,
                    'response': token
                },
                timeout=5
            )
            result = response.json()
            return result.get('success', False)
        except:
            return False


class SignupForm(ReCAPTCHAMixin, UserCreationForm):
    """
    فرم ثبت‌نام کاربر جدید
    """
    first_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control h-56-px bg-neutral-50 radius-12',
            'placeholder': 'نام'
        }),
        label='نام'
    )

    last_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control h-56-px bg-neutral-50 radius-12',
            'placeholder': 'نام خانوادگی'
        }),
        label='نام خانوادگی'
    )

    phone_number = forms.CharField(
        max_length=11,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control h-56-px bg-neutral-50 radius-12',
            'placeholder': '09123456789',
            'pattern': '09[0-9]{9}'
        }),
        label='شماره تلفن',
        help_text='شماره باید با 09 شروع شود'
    )

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control h-56-px bg-neutral-50 radius-12',
            'placeholder': 'example@email.com'
        }),
        label='ایمیل'
    )

    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control h-56-px bg-neutral-50 radius-12',
            'placeholder': 'رمز عبور',
            'id': 'password1'
        }),
        label='رمز عبور',
        help_text='حداقل 8 کاراکتر'
    )

    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control h-56-px bg-neutral-50 radius-12',
            'placeholder': 'تکرار رمز عبور',
            'id': 'password2'
        }),
        label='تکرار رمز عبور'
    )

    profile_picture = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        }),
        label='عکس پروفایل (اختیاری)'
    )

    recaptcha_token = forms.CharField(
        widget=forms.HiddenInput(),
        required=True
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'phone_number',
                  'email', 'password1', 'password2', 'profile_picture']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control h-56-px bg-neutral-50 radius-12',
            'placeholder': 'نام کاربری'
        })

    def clean_recaptcha_token(self):
        """بررسی reCAPTCHA"""
        token = self.cleaned_data.get('recaptcha_token')
        if not self.verify_recaptcha(token):
            raise ValidationError('لطفاً تایید کنید که ربات نیستید')
        return token

    def clean_phone_number(self):
        """بررسی یکتا بودن شماره تلفن"""
        phone = self.cleaned_data.get('phone_number')
        if User.objects.filter(phone_number=phone).exists():
            raise ValidationError('این شماره تلفن قبلاً ثبت شده است')
        return phone

    def clean_email(self):
        """بررسی یکتا بودن ایمیل"""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('این ایمیل قبلاً ثبت شده است')
        return email


class LoginForm(ReCAPTCHAMixin, AuthenticationForm):
    """
    فرم ورود کاربر
    """
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control h-56-px bg-neutral-50 radius-12',
            'placeholder': 'نام کاربری یا ایمیل',
            'autofocus': True
        }),
        label='نام کاربری یا ایمیل'
    )

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control h-56-px bg-neutral-50 radius-12',
            'placeholder': 'رمز عبور',
            'id': 'login-password'
        }),
        label='رمز عبور'
    )

    recaptcha_token = forms.CharField(
        widget=forms.HiddenInput(),
        required=True
    )

    def clean_recaptcha_token(self):
        """بررسی reCAPTCHA"""
        token = self.cleaned_data.get('recaptcha_token')
        if not self.verify_recaptcha(token):
            raise ValidationError('لطفاً تایید کنید که ربات نیستید')
        return token


class OTPVerifyForm(forms.Form):
    """
    فرم تایید کد OTP
    """
    otp_code = forms.CharField(
        max_length=6,
        min_length=6,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control h-56-px bg-neutral-50 radius-12 text-center',
            'placeholder': '______',
            'pattern': '[0-9]{6}',
            'maxlength': '6',
            'autocomplete': 'off',
            'inputmode': 'numeric'
        }),
        label='کد تایید 6 رقمی'
    )

    def clean_otp_code(self):
        """بررسی فرمت کد OTP"""
        code = self.cleaned_data.get('otp_code')
        if not code.isdigit():
            raise ValidationError('کد OTP باید فقط شامل اعداد باشد')
        return code


class ProfileEditForm(forms.ModelForm):
    """
    فرم ویرایش پروفایل کاربر
    """
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone_number', 'profile_picture']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control h-56-px bg-neutral-50 radius-12',
                'placeholder': 'نام'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control h-56-px bg-neutral-50 radius-12',
                'placeholder': 'نام خانوادگی'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control h-56-px bg-neutral-50 radius-12',
                'placeholder': '09123456789',
                'pattern': '09[0-9]{9}'
            }),
            'profile_picture': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            })
        }
        labels = {
            'first_name': 'نام',
            'last_name': 'نام خانوادگی',
            'phone_number': 'شماره تلفن',
            'profile_picture': 'عکس پروفایل'
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean_phone_number(self):
        """بررسی یکتا بودن شماره (به جز کاربر فعلی)"""
        phone = self.cleaned_data.get('phone_number')
        if self.user:
            if User.objects.filter(phone_number=phone).exclude(pk=self.user.pk).exists():
                raise ValidationError('این شماره تلفن قبلاً ثبت شده است')
        return phone


class ChangePasswordForm(forms.Form):
    """
    فرم تغییر رمز عبور
    """
    current_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control h-56-px bg-neutral-50 radius-12',
            'placeholder': 'رمز عبور فعلی'
        }),
        label='رمز عبور فعلی'
    )

    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control h-56-px bg-neutral-50 radius-12',
            'placeholder': 'رمز عبور جدید'
        }),
        label='رمز عبور جدید',
        help_text='حداقل 8 کاراکتر'
    )

    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control h-56-px bg-neutral-50 radius-12',
            'placeholder': 'تکرار رمز عبور جدید'
        }),
        label='تکرار رمز عبور جدید'
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_current_password(self):
        """بررسی صحت رمز فعلی"""
        password = self.cleaned_data.get('current_password')
        if not self.user.check_password(password):
            raise ValidationError('رمز عبور فعلی اشتباه است')
        return password

    def clean(self):
        """بررسی یکسان بودن رمزهای جدید"""
        cleaned_data = super().clean()
        password1 = cleaned_data.get('new_password1')
        password2 = cleaned_data.get('new_password2')

        if password1 and password2 and password1 != password2:
            raise ValidationError('رمزهای عبور جدید یکسان نیستند')

        return cleaned_data

    def save(self):
        """ذخیره رمز عبور جدید"""
        self.user.set_password(self.cleaned_data['new_password1'])
        self.user.save()
        return self.user
