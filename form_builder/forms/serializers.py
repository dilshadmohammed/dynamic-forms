from rest_framework import serializers
from user.models import User
from .models import Form,FormField,FormResponse,Choice,ChoiceAnswer,LongAnswer,ShortAnswer,CheckBox,DateTable,FileTable
from utils.types import FormType
from utils.utils import sort_nested_list

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
        # Create the form with the user
        return Form.objects.create(**validated_data)

    def update(self, instance, validated_data):
        # Update the form instance
        instance.title = validated_data.get('title', instance.title)
        instance.description = validated_data.get('description', instance.description)
        instance.save()
        return instance

class ChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = ['id','text']



class FormFieldSerializer(serializers.ModelSerializer):
    choices = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        write_only=True
    )

    class Meta:
        model = FormField
        fields = "__all__"
        read_only_fields = ['id','form']
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.type in [FormType.RADIO_BUTTON,FormType.MULTIPLE_CHOICE,FormType.DROPDOWN]:
            representation['choices'] = ChoiceSerializer(instance.choices.all(), many=True).data
        return representation
    

    def create(self, validated_data):
        form = self.context['form']
        choices_data = validated_data.pop('choices', None)
        form_field = FormField.objects.create(form=form, **validated_data)
        if choices_data and validated_data['type'] in [FormType.RADIO_BUTTON,FormType.MULTIPLE_CHOICE,FormType.DROPDOWN]:
            for choice_data in choices_data:
                Choice.objects.create(formfield=form_field, text=choice_data)
        return form_field
    
    def update(self, instance, validated_data):
        choices_data = validated_data.pop('choices', None)
        instance = super().update(instance, validated_data)
        if choices_data and instance.type in [FormType.RADIO_BUTTON,FormType.MULTIPLE_CHOICE,FormType.DROPDOWN]:
            # Optionally handle choices update logic
            instance.choices.all().delete()  # Clear existing choices
            for choice_data in choices_data:
                Choice.objects.create(formfield=instance, text=choice_data)
        return instance
        
        
    
class FormDetailSerializer(serializers.ModelSerializer):
    form_fields = FormFieldSerializer(many=True)
    
    class Meta:
        model=Form
        exclude=['user']
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)

        # Sort form fields by ID
        representation['form_fields'] = sorted(
            representation['form_fields'],
            key=lambda x: x['id']
        )

        # Recursively sort lists within form fields
        for field in representation['form_fields']:
            sort_nested_list(field)

        return representation