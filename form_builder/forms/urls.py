from rest_framework.routers import DefaultRouter
from django.urls import path
from .views import FormViewSet,FormResponseAPI

router = DefaultRouter()
router.register(r'form-editor', FormViewSet, basename='form')

urlpatterns = [
    path('view/<str:pk>',FormResponseAPI.as_view(),name='form-view')
    ]

urlpatterns += router.urls