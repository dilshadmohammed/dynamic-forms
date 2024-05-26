import decouple
import jwt
import pytz
from datetime import datetime, timedelta
from .types import TokenType
from user.models import Token
from form_builder.settings import SECRET_KEY

def format_time(date_time):
    formated_time = date_time.strftime("%Y-%m-%d %H:%M:%S%z")
    return datetime.strptime(formated_time, "%Y-%m-%d %H:%M:%S%z")


def get_utc_time() -> datetime:
    
    local_now = datetime.now(pytz.timezone("UTC"))
    return format_time(local_now)


def string_to_date_time(dt_str):
    return datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S%z")


def generate_jwt(user):
    access_expiry_time = get_utc_time() + timedelta(seconds=10800)
    access_expiry = str(format_time(access_expiry_time))
    
    refresh_expiry_time = get_utc_time() + timedelta(days=7)
    refresh_expiry = str(format_time(refresh_expiry_time))
    
    access_token = jwt.encode(
        {
            'id':user.id,
            'expiry':access_expiry,
            'tokenType':'access'
        },
        decouple.config('SECRET_KEY'),
        algorithm="HS256"
    )
    
    refresh_token = jwt.encode(
        {
            'id':user.id,
            'expiry':refresh_expiry,
            'tokenType':'refresh'
        },
        decouple.config('SECRET_KEY'),
        algorithm="HS256"
    )
    
    
    return access_token,refresh_token


def get_refresh_expiry(token):
     payload = jwt.decode(
            token, SECRET_KEY, algorithms=["HS256"], verify=True
        )
     expiry = datetime.strptime(payload.get("expiry"), "%Y-%m-%d %H:%M:%S%z")
     return expiry

    
def mark_token_expired(token,user,token_type,expiry):
    Token.objects.create(user=user,token=token,token_type=token_type,expiry=expiry)