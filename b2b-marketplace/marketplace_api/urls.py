
"""
marketplace_api URL Configuration
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/accounts/', include('apps.accounts.urls')),
    path('api/v1/listings/', include('apps.listings.urls')),
    path('api/v1/orders/', include('apps.orders.urls')),
    path('api/v1/collaborations/', include('apps.collaborations.urls')),
    path('api/v1/reviews/', include('apps.reviews_ratings.urls')),
    path('api/v1/community/', include('apps.community_engagement.urls')),
    path('api/v1/payments/', include('apps.payments_monetization.urls')),
    # path('api/v1/analytics/', include('apps.analytics_ai.urls')), # Add if analytics_ai has URLs

    # For DRF browsable API login/logout
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Optional: Add a health check endpoint
from django.http import HttpResponse
urlpatterns += [path("health/", lambda r: HttpResponse("OK"))]