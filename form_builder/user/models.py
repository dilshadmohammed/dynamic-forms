import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser


class User(AbstractBaseUser):
    id = models.CharField(primary_key=True, max_length=36, default=uuid.uuid4)
    username = models.CharField(max_length=100, unique=True)
    email = models.EmailField(max_length=255, unique=True)
    password = models.CharField(max_length=200, blank=True, null=True)
    

    # Required fields for createsuperuser command
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

