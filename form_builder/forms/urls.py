from django.urls import path
from .views import TestAPI

urlpatterns = [
    path('testview/',TestAPI.as_view(),name='test-view')
]