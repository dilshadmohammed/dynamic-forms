from django.urls import path
from .views import *

urlpatterns = [
    path('', FormListView.as_view(), name='form-list'),
    path('create/', FormCreateView.as_view(), name='form-create'),
    path('<str:pk>/', FormRetrieveView.as_view(), name='form-detail'),
    path('<str:pk>/update/', FormUpdateView.as_view(), name='form-update'),
    path('<str:pk>/delete/', FormDeleteView.as_view(), name='form-delete'),
    path('<str:pk>/add_field/', AddFieldView.as_view(), name='add-field'),
    path('<str:pk>/edit_field/<str:field_pk>/', EditFieldView.as_view(), name='edit-field'),
    path('<str:pk>/delete_field/<str:field_pk>/', DeleteFieldView.as_view(), name='delete-field'),
    path('view/<str:pk>/',FormResponseAPI.as_view(),name='form-view'),
    path('view_response/<str:pk>/', FormResponseDetail.as_view(), name='view-response')
    ]
