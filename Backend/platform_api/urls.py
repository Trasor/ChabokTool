# platform_api/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

# تغییر عنوان admin
admin.site.site_header = "پنل مدیریت ChabokTool"
admin.site.site_title = "ChabokTool Admin"
admin.site.index_title = "خوش آمدید به پنل مدیریت"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('core/', include('core.urls')),
    path('api/accounts/', include('accounts.urls')),
    path('api/modules/', include('modules.urls')),
    path('', TemplateView.as_view(template_name='index.html'), name='home'),
]

# Static files برای development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)