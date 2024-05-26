from django.urls import path
from .views import UserRegisterAPI, UserAuthAPI, GetAcessToken,UserLogoutAPI

urlpatterns = [
    path('register/', UserRegisterAPI.as_view(), name='user-register'),
    path('auth/', UserAuthAPI.as_view(), name='user-auth'),
    path('get-access-token/', GetAcessToken.as_view(), name='user-auth'),
    path('logout/', UserLogoutAPI.as_view(), name='user-auth'),
]
