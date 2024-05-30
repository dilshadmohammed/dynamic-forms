from rest_framework import serializers
from user.models import User
from .models import Form,FormField,FormResponse,Choice,ChoiceAnswer,LongAnswer,ShortAnswer,CheckBox,Dropdown,DateTable,FileTable
from utils.types import FormType

class UserRetrievalSerializer(serializers.ModelSerializer):

    class Meta:
        model=User
        exclude=['password']
        
class FormListSerializer(serializers.ModelSerializer):
    
    class Meta:
        model=Form
        exclude=['user']

class FormCUDSerializer(serializers.ModelSerializer):
    title = serializers.CharField(required=False, default='Untitled-form')
    description = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Form
        fields = ['title', 'description']

    def create(self, validated_data):
        # Get the user from the request context
        user = self.context['user']
        # Create the form with the user
        return Form.objects.create(user=User.objects.get(id=user), **validated_data)

    def update(self, instance, validated_data):
        # Update the form instance
        instance.title = validated_data.get('title', instance.title)
        instance.description = validated_data.get('description', instance.description)
        instance.save()
        return instance


class FormFieldSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = FormField
        fields = "__all__"
        read_only_fields = ['id','form']
    
    def create(self,validated_data):
        form = self.context['form']
        return FormField.objects.create(form=form,**validated_data)
        
        
    
class FormDetailSerializer(serializers.ModelSerializer):
    form_fields = FormFieldSerializer(many=True)
    
    class Meta:
        model=Form
        exclude=['user']