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


from utils.views import get_utc_time,generate_jwt
from .models import User
from .serializers import UserSerializer


class UserRegisterAPI(APIView):
    def post(self,request):
        data = request.data
        data = {key: value for key, value in data.items() if value}
        
        created_user = UserSerializer(data=data)
        
        if not created_user.is_valid():
            return Response({
                "general_message":created_user.errors
            },
            status=status.HTTP_400_BAD_REQUEST
            )
        user = created_user.save()
        
        access_token,refresh_token = generate_jwt(user)
                
        
        res_data = {
            "user": UserSerializer(user).data,
            "accessToken":access_token,
            "refreshToken":refresh_token
        }
        
        return Response(res_data,status=status.HTTP_200_OK)

        

class UserAuthAPI(APIView):
    def post(self,request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        user = User.objects.filter(Q(username=username) | Q(email=username)).first()
        if user:
            if user.password and check_password(password,user.password):
                access_token,refresh_token = generate_jwt(user)
                
                return Response(
                    {
                        "accessToken":access_token,
                        "refreshToken":refresh_token
                    },
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {
                        "general_message":"Invalid Password"
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            return Response(
                    {
                        "general_message":"Invalid username or email"
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
        