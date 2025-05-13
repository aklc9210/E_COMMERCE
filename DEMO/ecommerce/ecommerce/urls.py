from django.contrib import admin
from django.urls import path, include
from rest_framework import routers

router = routers.DefaultRouter()
# router.register(r'model1', YourViewSet1)
# router.register(r'model2', YourViewSet2)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('app.urls')), 
    # path('api/auth/', include('rest_framework.urls')),  # login/logout trang DRF
]