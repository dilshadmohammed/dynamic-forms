import datetime
import decouple
from datetime import datetime

import jwt
from django.conf import settings
from django.http import HttpRequest
from rest_framework import authentication
from rest_framework.authentication import get_authorization_header
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import BasePermission
from form_builder.settings import SECRET_KEY

def format_time(date_time):
    formatted_time = date_time.strftime("%Y-%m-%d %H:%M:%S%z")
    return datetime.strptime(formatted_time, "%Y-%m-%d %H:%M:%S%z")


class CustomizePermission(BasePermission):
    token_prefix = "Bearer"

    def authenticate(self, request):
        return JWTUtils.is_jwt_authenticated(request)

    def authenticate_header(self, request):
        return f'{self.token_prefix} realm="api"'
    
class JWTUtils:
    @staticmethod
    def fetch_user_id(request):
        token = authentication.get_authorization_header(request).decode("utf-8").split()
        payload = jwt.decode(
            token[1], settings.SECRET_KEY, algorithms=["HS256"], verify=True
        )
        user_id = payload.get("id")
        if user_id is None:
            raise Exception(
                "The corresponding JWT token does not contain the 'user_id' key"
            )
        return user_id
    

    @staticmethod
    def is_jwt_authenticated(request):
        token_prefix = "Bearer"
        try:
            auth_header = get_authorization_header(request).decode("utf-8")
            if not auth_header or not auth_header.startswith(token_prefix):
                raise UnauthorizedAccessException("Invalid token header")

            token = auth_header[len(token_prefix):].strip()
            if not token:
                raise UnauthorizedAccessException("Empty Token")

            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"], verify=True)

            user_id = payload.get("id")
            expiry = datetime.strptime(payload.get("expiry"), "%Y-%m-%d %H:%M:%S%z")

            if not user_id or expiry < DateTimeUtils.get_current_utc_time():
                raise UnauthorizedAccessException("Token Expired or Invalid")

            return None, payload
        except jwt.exceptions.InvalidSignatureError as e:
            raise UnauthorizedAccessException(
                {
                    "hasError": True,
                    "message": {"general": [str(e)]},
                    "statusCode": 1000,
                }
            ) from e
        except jwt.exceptions.DecodeError as e:
            raise UnauthorizedAccessException(
                {
                    "hasError": True,
                    "message": {"general": [str(e)]},
                    "statusCode": 1000,
                }
            ) from e
        except AuthenticationFailed as e:
            raise UnauthorizedAccessException(str(e)) from e
        except Exception as e:
            raise UnauthorizedAccessException(
                {
                    "hasError": True,
                    "message": {"general": [str(e)]},
                    "statusCode": 1000,
                }
            ) from e
            
            
    @staticmethod
    def is_logged_in(request):
        try:
            JWTUtils.is_jwt_authenticated(request)
            return True
        except UnauthorizedAccessException:
            return False