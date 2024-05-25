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


from utils.utils import get_utc_time,generate_jwt,format_time
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
            

class GetAcessToken(APIView):
    
    def post(self,request):
        refresh_token = request.data.get('refreshToken')
        try:
            payload = jwt.decode(refresh_token,decouple.config('SECRET_KEY'),algorithms="HS256",verify=True)
        except Exception as e:
            return Response({"message":str(e)})
        
        user_id = payload.get('id')
        token_type = payload.get('tokenType')
        
        if token_type != "refresh":
            return Response({"message":"Invalid refresh token"})
        
        if user_id:
            user = User.objects.filter(id=user_id).first()
            if not user:
                return Response({"message":"User Invalid"})

            access_expiry_time = get_utc_time() + timedelta(seconds=10800)
            access_expiry = str(format_time(access_expiry_time))
            
            access_token = jwt.encode(
                {
                    'id':user.id,
                    'expiry':access_expiry,
                    'tokenType':'access'
                },
                decouple.config('SECRET_KEY'),
                algorithm="HS256"
            )
            
            return Response({'accessToken': access_token, 'refreshToken': refresh_token,'expiry': access_expiry})
        else:
            return Response({"message":"Invalid refresh token"})

