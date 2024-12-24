# from django.contrib import admin
# from django.urls import path,include
# from app_streaming.views import VideoStreamView

# urlpatterns = [
#     path('admin/', admin.site.urls),
#     path('app_streaming/', include('app_streaming.urls')),  # Make sure your app URLs are included here
#     path('api/stream/', VideoStreamView.as_view(), name='stream-api'),
# ]

from django.contrib import admin
from django.urls import path, include
from app_streaming.views import home

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('app_streaming/', include('app_streaming.urls')),
]



