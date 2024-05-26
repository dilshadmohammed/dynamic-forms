from django.utils import timezone
from .models import Token

def cleanup_expired_tokens():
    expired_tokens = Token.objects.filter(expiry_time__lt=timezone.now())
    expired_tokens.delete()