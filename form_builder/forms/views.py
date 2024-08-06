import decouple
import jwt
import pytz
import uuid
from datetime import timedelta
from decouple import config
from django.contrib.auth.hashers import check_password
from django.db.models import Q
from django.shortcuts import reverse
from rest_framework import status
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



class FormListView(APIView):
    authentication_classes = [JWTAuth]
    
    def get(self, request, *args, **kwargs):
        try:
            user_id = JWTUtils.fetch_user_id(request)
            queryset = Form.objects.filter(user_id=user_id)
            serializer = FormListSerializer(queryset, many=True)
            return CustomResponse(response=serializer.data).get_success_response()
        except Exception as e:
            return CustomResponse(message=str(e)).get_failure_response()
        

class FormRetrieveView(APIView):
    authentication_classes = [JWTAuth]
    
    def get(self, request, pk, *args, **kwargs):
        try:
            user_id = JWTUtils.fetch_user_id(request)
            form = Form.objects.get(pk=pk, user_id=user_id)
            serializer = FormDetailSerializer(form)
            return CustomResponse(response=serializer.data).get_success_response()
        except Form.DoesNotExist:
            return CustomResponse(message="Form not found").get_failure_response(status_code=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return CustomResponse(message=str(e)).get_failure_response()
        

class FormCreateView(APIView):
    authentication_classes = [JWTAuth]
    
    def post(self, request, *args, **kwargs):
        serializer = FormCUDSerializer(data=request.data)
        if serializer.is_valid():
            user_id = JWTUtils.fetch_user_id(request)
            serializer.save(user_id=user_id)
            return CustomResponse(response=serializer.data).get_success_response()
        else:
            return CustomResponse(message=serializer.errors).get_failure_response()
        
        
class FormUpdateView(APIView):
    authentication_classes = [JWTAuth]
    
    def put(self, request, pk, *args, **kwargs):
        try:
            user_id = JWTUtils.fetch_user_id(request)
            form = Form.objects.get(pk=pk, user_id=user_id)
            serializer = FormCUDSerializer(form, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save(user_id=user_id)
                return CustomResponse(response=serializer.data).get_success_response()
            else:
                return CustomResponse(message=serializer.errors).get_failure_response()
        except Form.DoesNotExist:
            return CustomResponse(message="Form not found").get_failure_response(status_code=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return CustomResponse(message=str(e)).get_failure_response()
        

class FormDeleteView(APIView):
    authentication_classes = [JWTAuth]
    
    def delete(self, request, pk, *args, **kwargs):
        try:
            user_id = JWTUtils.fetch_user_id(request)
            form = Form.objects.get(pk=pk, user_id=user_id)
            form.delete()
            return CustomResponse(message="Form deleted successfully").get_success_response()
        except Form.DoesNotExist:
            return CustomResponse(message="Form not found").get_failure_response(status_code=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return CustomResponse(message=str(e)).get_failure_response(status_code=status.HTTP_400_BAD_REQUEST)
        
class AddFieldView(APIView):
    authentication_classes = [JWTAuth]
    
    def post(self, request, pk, *args, **kwargs):
        user_id = JWTUtils.fetch_user_id(request)
        try:
            form = Form.objects.get(pk=pk, user_id=user_id)
        except Form.DoesNotExist:
            return CustomResponse(message="Form not found").get_failure_response(status_code=status.HTTP_404_NOT_FOUND)
        
        serializer = FormFieldSerializer(data=request.data, context={'form': form})
        if serializer.is_valid():
            serializer.save()
            return CustomResponse(message="Form field added").get_success_response()
        else:
            return CustomResponse(message=serializer.errors).get_failure_response()
        
        
class EditFieldView(APIView):
    authentication_classes = [JWTAuth]
    
    def put(self, request, pk, field_pk, *args, **kwargs):
        user_id = JWTUtils.fetch_user_id(request)
        
        try:
            formfield = FormField.objects.select_related('form').get(pk=field_pk)
        except FormField.DoesNotExist:
            return CustomResponse(message="Form field does not exist").get_failure_response(status_code=status.HTTP_404_NOT_FOUND)
        
        if formfield.form.user_id != user_id or formfield.form.id != pk:
            return CustomResponse(message="Form field does not exist").get_failure_response(status_code=status.HTTP_404_NOT_FOUND)
        
        serializer = FormFieldSerializer(formfield, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return CustomResponse(message="Form field edited").get_success_response()
        else:
            return CustomResponse(message=serializer.errors).get_failure_response()
        
        
class DeleteFieldView(APIView):
    authentication_classes = [JWTAuth]
    
    def delete(self, request, pk, field_pk, *args, **kwargs):
        user_id = JWTUtils.fetch_user_id(request)
        
        try:
            formfield = FormField.objects.select_related('form').get(pk=field_pk)
        except FormField.DoesNotExist:
            return CustomResponse(message="Form field does not exist").get_failure_response()
        
        if formfield.form.user_id != user_id or formfield.form.id != pk:
            return CustomResponse(message="Form field does not exist").get_failure_response()
        
        formfield.delete()
        return CustomResponse(message="Form field deleted successfully").get_success_response()
    


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
        
        