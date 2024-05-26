import decouple
import jwt
import pytz
import uuid
from datetime import timedelta
from decouple import config
from django.contrib.auth.hashers import check_password
from django.db.models import Q
from django.shortcuts import reverse
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from utils.permission import JWTAuth
from .serializers import UserRetrievalSerializer
from user.models import User
from utils.permission import JWTUtils
# Create your views here.
class TestAPI(APIView):
    authentication_classes = [JWTAuth]
    
    def get(self, request):
        user_id = JWTUtils.fetch_user_id(request)
        user = User.objects.filter(id=user_id).first() 
        if user:
            serializer = UserRetrievalSerializer(user)
            return Response({"message": "Response general", "user": serializer.data})
        else:
            return Response({"message": "User not found"}, status=404)