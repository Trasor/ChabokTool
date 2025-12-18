from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User

def forgotPassword(request):
    return render(request, "authentication/forgotPassword.html")

def signin(request):
    if request.user.is_authenticated:
        return redirect('index')
    
    if request.method == 'POST':
        username_or_email = request.POST.get('username')
        password = request.POST.get('password')
        
        # سعی کن با username
        user = authenticate(request, username=username_or_email, password=password)
        
        # اگه نشد، سعی کن با email
        if user is None:
            try:
                user_obj = User.objects.get(email=username_or_email)
                user = authenticate(request, username=user_obj.username, password=password)
            except User.DoesNotExist:
                user = None
        
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', 'index')
            return redirect(next_url)
        else:
            messages.error(request, 'نام کاربری/ایمیل یا رمز عبور اشتباه است!')
    
    return render(request, "authentication/signin.html")

def signup(request):
    return render(request, "authentication/signup.html")

def signout(request):
    logout(request)
    return redirect('signin')