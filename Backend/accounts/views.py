from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import User, UserProfile
import json

def register_view(request):
    """صفحه ثبت نام"""
    if request.method == 'POST':
        if request.content_type == 'application/json':
            # API request
            data = json.loads(request.body)
            email = data.get('email')
            username = data.get('username')
            password = data.get('password')
            first_name = data.get('first_name', '')
            last_name = data.get('last_name', '')
            
            # بررسی وجود کاربر
            if User.objects.filter(email=email).exists():
                return JsonResponse({'error': 'این ایمیل قبلاً ثبت شده است'}, status=400)
            
            if User.objects.filter(username=username).exists():
                return JsonResponse({'error': 'این نام کاربری قبلاً گرفته شده است'}, status=400)
            
            # ایجاد کاربر
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            
            # ایجاد پروفایل
            UserProfile.objects.create(user=user)
            
            return JsonResponse({
                'success': True,
                'message': 'ثبت نام با موفقیت انجام شد',
                'user_id': user.id
            })
        
        else:
            # Form request
            email = request.POST.get('email')
            username = request.POST.get('username')
            password = request.POST.get('password')
            first_name = request.POST.get('first_name', '')
            last_name = request.POST.get('last_name', '')
            
            if User.objects.filter(email=email).exists():
                messages.error(request, 'این ایمیل قبلاً ثبت شده است')
                return render(request, 'accounts/register.html')
            
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            
            UserProfile.objects.create(user=user)
            
            messages.success(request, 'ثبت نام با موفقیت انجام شد. حالا می‌توانید وارد شوید.')
            return redirect('login')
    
    return render(request, 'accounts/register.html')

def login_view(request):
    """صفحه ورود"""
    if request.method == 'POST':
        if request.content_type == 'application/json':
            # API request
            data = json.loads(request.body)
            email = data.get('email')
            password = data.get('password')
            
            try:
                user = User.objects.get(email=email)
                user = authenticate(request, username=user.username, password=password)
                
                if user:
                    login(request, user)
                    return JsonResponse({
                        'success': True,
                        'message': 'ورود موفقیت‌آمیز',
                        'user': {
                            'id': user.id,
                            'username': user.username,
                            'email': user.email,
                            'full_name': user.get_full_name()
                        }
                    })
                else:
                    return JsonResponse({'error': 'ایمیل یا رمز عبور اشتباه است'}, status=400)
            
            except User.DoesNotExist:
                return JsonResponse({'error': 'ایمیل یا رمز عبور اشتباه است'}, status=400)
        
        else:
            # Form request
            email = request.POST.get('email')
            password = request.POST.get('password')
            
            try:
                user = User.objects.get(email=email)
                user = authenticate(request, username=user.username, password=password)
                
                if user:
                    login(request, user)
                    return redirect('profile')
                else:
                    messages.error(request, 'ایمیل یا رمز عبور اشتباه است')
            
            except User.DoesNotExist:
                messages.error(request, 'ایمیل یا رمز عبور اشتباه است')
    
    return render(request, 'accounts/login.html')

@login_required
def profile_view(request):
    """صفحه پروفایل کاربر"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        # بروزرسانی پروفایل
        request.user.first_name = request.POST.get('first_name', '')
        request.user.last_name = request.POST.get('last_name', '')
        request.user.phone = request.POST.get('phone', '')
        request.user.company_name = request.POST.get('company_name', '')
        request.user.website = request.POST.get('website', '')
        request.user.save()
        
        profile.bio = request.POST.get('bio', '')
        profile.address = request.POST.get('address', '')
        profile.city = request.POST.get('city', '')
        profile.email_notifications = request.POST.get('email_notifications') == 'on'
        profile.sms_notifications = request.POST.get('sms_notifications') == 'on'
        profile.save()
        
        messages.success(request, 'پروفایل با موفقیت بروزرسانی شد')
    
    context = {
        'user': request.user,
        'profile': profile
    }
    
    return render(request, 'accounts/profile.html', context)

def logout_view(request):
    """خروج کاربر"""
    logout(request)
    messages.success(request, 'با موفقیت خارج شدید')
    return redirect('home')
