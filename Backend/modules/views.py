from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Module, ModuleCategory, UserModule

def module_list(request):
    """لیست ماژول‌ها - API"""
    modules = Module.objects.filter(status='active')
    
    # فیلتر بر اساس دسته‌بندی
    category = request.GET.get('category')
    if category:
        modules = modules.filter(category__slug=category)
    
    modules_data = []
    for module in modules:
        modules_data.append({
            'id': str(module.id),
            'name': module.name,
            'short_description': module.short_description,
            'price': int(module.price),
            'pricing_type': module.get_pricing_type_display(),
            'module_type': module.get_module_type_display(),
            'category': module.category.name,
            'is_featured': module.is_featured,
            'is_popular': module.is_popular,
            'features': module.get_features_list()[:3],  # فقط 3 ویژگی اول
            'demo_url': module.demo_url
        })
    
    return JsonResponse({'modules': modules_data})

def module_detail(request, module_id):
    """جزئیات ماژول"""
    module = get_object_or_404(Module, id=module_id, status='active')
    
    # بررسی خرید کاربر
    user_has_module = False
    if request.user.is_authenticated:
        user_has_module = UserModule.objects.filter(
            user=request.user, 
            module=module, 
            is_active=True
        ).exists()
    
    data = {
        'id': str(module.id),
        'name': module.name,
        'description': module.description,
        'short_description': module.short_description,
        'price': int(module.price),
        'pricing_type': module.get_pricing_type_display(),
        'module_type': module.get_module_type_display(),
        'category': module.category.name,
        'version': module.version,
        'features': module.get_features_list(),
        'requirements': module.requirements,
        'demo_url': module.demo_url,
        'download_count': module.download_count,
        'user_has_module': user_has_module
    }
    
    return JsonResponse(data)

def categories_list(request):
    """لیست دسته‌بندی‌ها"""
    categories = ModuleCategory.objects.filter(is_active=True)
    
    categories_data = []
    for category in categories:
        categories_data.append({
            'slug': category.slug,
            'name': category.name,
            'description': category.description,
            'icon': category.icon,
            'color': category.color,
            'modules_count': category.module_set.filter(status='active').count()
        })
    
    return JsonResponse({'categories': categories_data})

@login_required
def user_modules(request):
    """ماژول‌های خریداری شده توسط کاربر"""
    user_modules = UserModule.objects.filter(user=request.user, is_active=True)
    
    modules_data = []
    for user_module in user_modules:
        modules_data.append({
            'module': {
                'id': str(user_module.module.id),
                'name': user_module.module.name,
                'version': user_module.module.version,
                'type': user_module.module.get_module_type_display()
            },
            'license_key': user_module.license_key,
            'purchased_at': user_module.purchased_at.strftime('%Y/%m/%d'),
            'allowed_domains': user_module.get_allowed_domains_list(),
            'max_domains': user_module.max_domains,
            'expires_at': user_module.expires_at.strftime('%Y/%m/%d') if user_module.expires_at else None
        })
    
    return JsonResponse({'user_modules': modules_data})
