import decouple
import jwt
import pytz
import uuid
from datetime import datetime
from datetime import timedelta
from decouple import config
from django.contrib.auth.hashers import check_password
from django.db.models import Q
from django.shortcuts import reverse
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.authentication import get_authorization_header


from utils.utils import get_utc_time,generate_jwt,format_time,mark_token_expired,get_refresh_expiry
from utils.permission import JWTUtils
from utils.types import TokenType
from .models import User,Token
from .serializers import UserCUDSerializer


class UserRegisterAPI(APIView):
    def post(self,request):
        data = request.data
        data = {key: value for key, value in data.items() if value}
        
        created_user = UserCUDSerializer(data=data)
        
        if not created_user.is_valid():
            return Response({
                "general_message":created_user.errors
            },
            status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response({"message":"User created successfully"},status=status.HTTP_200_OK)

        

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
            
            

class UserLogoutAPI(APIView):
    def post(self,request):
        
        user_id = JWTUtils.fetch_user_id(request)
        if not user_id:
            return Response({"message": "Invalid user"}, status=400)
        user = User.objects.filter(id=user_id).first()
        
        if not user:
            return Response({"message": "Invalid user"}, status=400)

        refresh_token = request.data.get('refreshToken')
        access_token = get_authorization_header(request).decode("utf-8")[len("Bearer"):].strip()

        if not access_token:
            return Response({"message": "Access token is required"}, status=400)

        # access_token = access_token.encode('utf-8')  # Ensure the token is bytes
        access_expiry = JWTUtils.fetch_expiry(request)

        if refresh_token:
            # refresh_token = refresh_token.encode('utf-8')  # Ensure the token is bytes
            refresh_expiry = get_refresh_expiry(refresh_token)
            mark_token_expired(refresh_token, user, TokenType.REFRESH, refresh_expiry)

        mark_token_expired(access_token, user, TokenType.ACCESS, access_expiry)

        return Response({"message": "User logged out successfully"}, status=200)

        


class GetAcessToken(APIView):
    
    def post(self,request):
        refresh_token = request.data.get('refreshToken')
        
        existing_token = Token.objects.filter(token=refresh_token).first()
        if existing_token:
            return Response({"message": "Invalid or expired refresh token"}, status=400)
    
        try:
            payload = jwt.decode(refresh_token,decouple.config('SECRET_KEY'),algorithms="HS256",verify=True)
        except Exception as e:
            return Response({"message":str(e)})
        
        user_id = payload.get('id')
        token_type = payload.get('tokenType')
        expiry = datetime.strptime(payload.get("expiry"), "%Y-%m-%d %H:%M:%S%z")
        
        if token_type != "refresh" or expiry < get_utc_time():
            return Response({"message":"Invalid or expired refresh token"})
        
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

