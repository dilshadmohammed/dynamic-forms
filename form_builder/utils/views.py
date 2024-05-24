import decouple
import jwt
import pytz
from datetime import datetime, timedelta


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
            'expiry':access_expiry,
            'tokenType':'refresh'
        },
        decouple.config('SECRET_KEY'),
        algorithm="HS256"
    )
    
    return access_token,refresh_token

    
    