import decouple
import jwt
import pytz
import uuid
from datetime import timedelta
from decouple import config
from django.contrib.auth.hashers import check_password
from django.db.models import Q
from django.shortcuts import reverse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import Http404
from utils.permission import JWTAuth
from .serializers import UserRetrievalSerializer,FormListSerializer,FormCUDSerializer,FormDetailSerializer,FormFieldSerializer
from user.models import User
from .models import Form,FormField
from utils.permission import JWTUtils


# Create your views here.



class FormViewSet(viewsets.ModelViewSet):
    authentication_classes = [JWTAuth]
    http_method_names = ['get', 'post', 'put', 'delete'] 
    
    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return FormListSerializer if self.action == 'list' else FormDetailSerializer
        return FormCUDSerializer
    
    def get_queryset(self):
        user_id = JWTUtils.fetch_user_id(self.request)
        return Form.objects.filter(user=user_id)
    
    def perform_create(self, serializer):
        user_id = JWTUtils.fetch_user_id(self.request)
        serializer.save(user_id=user_id)
    
    def perform_update(self, serializer):
        user_id = JWTUtils.fetch_user_id(self.request)
        serializer.save(user_id=user_id)
    
    @action(detail=True, methods=['post'])
    def add_field(self, request, pk=None):
        user_id = JWTUtils.fetch_user_id(request)
        try:
            form = Form.objects.get(pk=pk, user_id=user_id)
        except Form.DoesNotExist:
            raise Http404("Form does not exist")
        
        serializer = FormFieldSerializer(data=request.data, context={'form': form})
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Form field added"}, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['put'], url_path='edit_field/(?P<field_pk>[^/.]+)')
    def edit_field(self, request, pk=None, field_pk=None):
        user_id = JWTUtils.fetch_user_id(request)
        try:
            formfield = FormField.objects.select_related('form').get(pk=field_pk)
        except FormField.DoesNotExist:
            raise Http404("Form field does not exist")
        
        if formfield.form.user_id != user_id:
            return Response({"error": "You do not have permission to edit this form field"}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = FormFieldSerializer(formfield, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Form field edited"}, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['delete'], url_path='delete_field/(?P<field_pk>[^/.]+)')
    def delete_field(self, request, pk=None, field_pk=None):
        user_id = JWTUtils.fetch_user_id(request)
        
        try:
            formfield = FormField.objects.select_related('form').get(pk=field_pk)
        except FormField.DoesNotExist:
            raise Http404("Form field does not exist")
        
        if formfield.form.user_id != user_id:
            return Response({"error": "You do not have permission to delete this form field"}, status=status.HTTP_403_FORBIDDEN)
        
        formfield.delete()
        return Response({"message": "Form field deleted successfully"}, status=status.HTTP_204_NO_CONTENT)