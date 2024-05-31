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
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import Http404
from utils.permission import JWTAuth
from .serializers import UserRetrievalSerializer,FormListSerializer,FormCUDSerializer,FormDetailSerializer,FormFieldSerializer,FormSubmissionSerializer,FormResponseSerializer
from user.models import User
from .models import Form,FormField,FormResponse
from utils.permission import JWTUtils
from utils.response import CustomResponse

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
        return Form.objects.filter(user_id=user_id)
    
    def perform_create(self, serializer):
        user_id = JWTUtils.fetch_user_id(self.request)
        serializer.save(user_id=user_id)
    
    def perform_update(self, serializer):
        user_id = JWTUtils.fetch_user_id(self.request)
        serializer.save(user_id=user_id)


    def list(self, request, *args, **kwargs):
        try:
            queryset = self.filter_queryset(self.get_queryset())
            serializer = self.get_serializer(queryset, many=True)
            
            return CustomResponse(response=serializer.data).get_success_response()
        except Exception as e:
            return CustomResponse(message=str(e)).get_failure_response()

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return CustomResponse(response=serializer.data).get_success_response()
        except Exception as e:
            return CustomResponse(message=str(e)).get_failure_response()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            return CustomResponse(response=serializer.data).get_success_response()
        else:
            return CustomResponse(message=serializer.errors).get_failure_response()
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            self.perform_update(serializer)
            return CustomResponse(response=serializer.data).get_success_response()
        else:
            return CustomResponse(message=serializer.errors).get_failure_response()
    
    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            self.perform_destroy(instance)
            return CustomResponse(message="Form deleted successfully").get_success_response()
        except Http404:
            return CustomResponse(message="Form not found").get_failure_response(status_code=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return CustomResponse(message=str(e)).get_failure_response(status_code=status.HTTP_400_BAD_REQUEST)

    
    @action(detail=True, methods=['post'])
    def add_field(self, request, pk=None):
        user_id = JWTUtils.fetch_user_id(request)
        try:
            form = Form.objects.get(pk=pk, user_id=user_id)
        except Form.DoesNotExist:
            return CustomResponse(message="form not found").get_failure_response(status_code=status.HTTP_404_NOT_FOUND)
        
        serializer = FormFieldSerializer(data=request.data, context={'form': form})
        if serializer.is_valid():
            serializer.save()
            return CustomResponse(message="Formfield added").get_success_response()
        else:
            return CustomResponse(message=serializer.errors).get_failure_response()
    
    @action(detail=True, methods=['put'], url_path='edit_field/(?P<field_pk>[^/.]+)')
    def edit_field(self, request, pk=None, field_pk=None):
        user_id = JWTUtils.fetch_user_id(request)
        
        try:
            formfield = FormField.objects.select_related('form').get(pk=field_pk)
        except FormField.DoesNotExist:
            return CustomResponse(message="formfield does not exits").get_failure_response(status_code=status.HTTP_404_NOT_FOUND)
        
        if formfield.form.user_id != user_id or formfield.form.id != pk:
            return CustomResponse(message="formfield does not exits").get_failure_response(status_code=status.HTTP_404_NOT_FOUND)
        
        serializer = FormFieldSerializer(formfield, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return CustomResponse(message="formfield edited").get_success_response()
        else:
            return CustomResponse(message=serializer.errors).get_failure_response()
    
    @action(detail=True, methods=['delete'], url_path='delete_field/(?P<field_pk>[^/.]+)')
    def delete_field(self, request, pk=None, field_pk=None):
        user_id = JWTUtils.fetch_user_id(request)
        
        try:
            formfield = FormField.objects.select_related('form').get(pk=field_pk)
        except FormField.DoesNotExist:
            return CustomResponse(message="Form field does not exist").get_failure_response()
        
        if formfield.form.user_id != user_id or formfield.form.id != pk:
            return CustomResponse(message="Form field does not exist").get_failure_response()
        
        formfield.delete()
        return CustomResponse(message="formfield deleted successfully").get_success_response()
    


class FormResponseAPI(APIView):
    
    def get(self, request, pk=None):
        if not pk:
            return CustomResponse(message="missing formID").get_failure_response()
        try:
            form = Form.objects.get(pk=pk)
        except Form.DoesNotExist:
            return CustomResponse(message="Form does not exits").get_failure_response(status_code=status.HTTP_404_NOT_FOUND)

        serializer = FormDetailSerializer(form)
        return Response(serializer.data)
    
    def post(self,request,pk = None):
        if not pk:
            return CustomResponse(message="missing formID").get_failure_response()
        serializer = FormSubmissionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors)
        
        
        
class FormResponseDetail(APIView):
        
    def get(self,request,pk=None):
        if not pk:
            return CustomResponse(message="missing responseID").get_failure_response()
        
        try:
            form_response = FormResponse.objects.get(pk=pk)
        except FormResponse.DoesNotExist:
            return CustomResponse(message="Response not found").get_failure_response(status_code=status.HTTP_404_NOT_FOUND)

        serializer = FormResponseSerializer(form_response)
        
        return CustomResponse(response=serializer.data).get_success_response()
        
        