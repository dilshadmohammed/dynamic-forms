from django.urls import path
from .views import UserRegisterAPI, UserAuthAPI

urlpatterns = [
    path('register/', UserRegisterAPI.as_view(), name='user-register'),
    path('auth/', UserAuthAPI.as_view(), name='user-auth'),
]
