from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    # 🕌 Halaman Admin Django
    path('admin/', admin.site.urls),

    # 🌐 Routing utama aplikasi "core"
    path('', include('core.urls')),

    # Redirect favicon agar tidak error di log
    path('favicon.ico', RedirectView.as_view(url='/static/favicon.ico', permanent=True)),
]

# ✅ Tambahan penting agar file PDF, Excel, dan gambar bisa diakses
# (hanya aktif saat DEBUG = True)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
