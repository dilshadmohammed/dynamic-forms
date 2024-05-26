from rest_framework import serializers
from user.models import User


class UserRetrievalSerializer(serializers.ModelSerializer):

    class Meta:
        model=User
        exclude=['password']