from rest_framework import serializers
from user.models import User
from .models import Form,FormField,FormResponse,Choice,ChoiceAnswer,LongAnswer,ShortAnswer,CheckBox,DateTable,FileTable,PaymentRequest
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
    upi_id = serializers.CharField(required=False,write_only=True)
    amount = serializers.CharField(required=False,write_only=True)
    
    is_required = serializers.BooleanField(required=False, allow_null=True)


    class Meta:
        model = FormField
        exclude = ['form']
        read_only_fields = ['id']
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.type in [FormType.RADIO_BUTTON,FormType.MULTIPLE_CHOICE,FormType.DROPDOWN]:
            representation['choices'] = ChoiceSerializer(instance.choices.all(), many=True).data
        if instance.type == FormType.UPI_PAYMENT:
            payment_details = instance.payment_details.first()
            if payment_details:
                representation['upi_id'] = payment_details.upi_id
                representation['amount'] = payment_details.amount
            else:
                representation['upi_id'] = None
                representation['amount'] = 0
        return representation
    

    def create(self, validated_data):
        form = self.context['form']
        choices_data = validated_data.pop('choices', None)
        upi_id = validated_data.pop('upi_id',None)
        amount = validated_data.pop('amount',None)
        if 'is_required' not in validated_data:
            validated_data['is_required'] = False
        form_field = FormField.objects.create(form=form, **validated_data)
        if choices_data and validated_data['type'] in [FormType.RADIO_BUTTON,FormType.MULTIPLE_CHOICE,FormType.DROPDOWN]:
            for choice_data in choices_data:
                Choice.objects.create(formfield=form_field, text=choice_data)
        if upi_id and amount and validated_data['type'] == FormType.UPI_PAYMENT:
            PaymentRequest.objects.create(formfield=form_field,upi_id=upi_id,amount=amount)
            
        return form_field
    
    def update(self, instance, validated_data):
        choices_data = validated_data.pop('choices', None)
        if not validated_data['is_required']:
            validated_data['is_required'] = instance.is_required
        instance = super().update(instance, validated_data)
        if choices_data and instance.type in [FormType.RADIO_BUTTON,FormType.MULTIPLE_CHOICE,FormType.DROPDOWN]:
            # Optionally handle choices update logic
            instance.choices.all().delete()  # Clear existing choices
            for choice_data in choices_data:
                Choice.objects.create(formfield=instance, text=choice_data)
        elif instance.type not in  [FormType.RADIO_BUTTON,FormType.MULTIPLE_CHOICE,FormType.DROPDOWN] and instance.choices.exists():
            instance.choices.all().delete()
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
    
    

class FormResponseValueSerializer(serializers.Serializer):
    id = serializers.CharField(required=True)
    value = serializers.CharField(required=True)

class FormSubmissionSerializer(serializers.Serializer):
    form = serializers.CharField(required=True)
    form_fields = FormResponseValueSerializer(many=True)

    def validate(self, data):
        """
        Custom validation to ensure that the provided responses are valid.
        """
        form_id = data.get('form')
        form_fields_response = data.get('form_fields')

        try:
            form = Form.objects.get(id=form_id)
        except Form.DoesNotExist:
            raise serializers.ValidationError("Form does not exist.")

        form_fields = FormField.objects.filter(form=form)
        form_field_ids = {str(field.id): field.type for field in form_fields}
        required_field_ids = {str(field.id): field.label for field in form_fields if field.is_required}
        response_field_ids = set(field.id for field in form_fields)

        for field_id, field in form_field_ids.items():
            if field_id in required_field_ids:
                # If a required field is missing from the response or has an empty value, raise an error
                if field_id not in response_field_ids or not field_id in {field.id for field in form_fields}:
                    raise serializers.ValidationError(f"Required field '{required_field_ids[field_id]}' is missing or has an empty value.")
        for response in form_fields_response:
            field_id = response.get('id')
            
            if field_id not in form_field_ids:
                raise serializers.ValidationError(f"Form field with ID '{field_id}' does not exist.")
            
            field_type = form_field_ids[field_id]
            
            if field_type in [FormType.RADIO_BUTTON, FormType.DROPDOWN]:
                if not isinstance(response.get('value'), str):
                    raise serializers.ValidationError(f"Invalid value type for choice field with ID '{field_id}'.")
                if not Choice.objects.filter(id=response.get('value'), formfield_id=field_id).exists():
                    raise serializers.ValidationError(f"Choice with ID '{choice_id}' does not exist for field with ID '{field_id}'.")
            
            elif field_type == FormType.MULTIPLE_CHOICE:
                if not isinstance(response.get('value'), (list, str)):
                    raise serializers.ValidationError(f"Invalid value type for multiple choice field with ID '{field_id}'. Expected a list or string.")
                if isinstance(response.get('value'), list):
                    for choice_id in response.get('value'):
                        if not Choice.objects.filter(id=choice_id, formfield_id=field_id).exists():
                            raise serializers.ValidationError(f"Choice with ID '{choice_id}' does not exist for field with ID '{field_id}'.")
                else:  # It's a string
                    choice_id = response.get('value')
                    if not Choice.objects.filter(id=choice_id, formfield_id=field_id).exists():
                        raise serializers.ValidationError(f"Choice with ID '{choice_id}' does not exist for field with ID '{field_id}'.")
            
            elif field_type == FormType.FILE_UPLOAD:
                if not isinstance(response.get('value'), str):  # Expecting a file path or URL as string
                    raise serializers.ValidationError(f"Invalid value type for file field with ID '{field_id}'.")

            elif field_type == FormType.DATE:
                try:
                    datetime.strptime(value, '%d-%m-%Y')  # Try 'dd-mm-yyyy' format
                except ValueError:
                    try:
                        datetime.strptime(value, '%d/%m/%Y')  # Try 'dd/mm/yyyy' format
                    except ValueError:
                        raise serializers.ValidationError(f"Invalid date format for date field with ID '{field_id}'. Expected format is 'DD-MM-YYYY' or 'DD/MM/YYYY'.")
                    
            elif field_type == FormType.CHECKBOX:
                if not isinstance(response.get('value'), bool):  # Expecting a boolean value
                    raise serializers.ValidationError(f"Invalid value type for checkbox field with ID '{field_id}'. Expected a boolean.")
            
            elif field_type in [FormType.SHORT_ANSWER,FormType.LONG_ANSWER]:
                if not isinstance(response.get('value'), str):
                    raise serializers.ValidationError(f"Invalid value type for short answer field with ID '{field_id}'.")
        return data

    def save(self):
        """
        Save the form responses to the database.
        """
        form_id = self.validated_data['form']
        form = Form.objects.get(pk=form_id)
        form_response = FormResponse.objects.create(form=form)
        form_fields = FormField.objects.filter(form=form)
        saved_responses = []

        for response_data in self.validated_data['form_fields']:
            field_id = response_data['id']
            field_type = form_fields.get(id=field_id).type
            field_value = response_data['value']

            if field_type == FormType.RADIO_BUTTON or field_type == FormType.DROPDOWN:
                choice_id = field_value
                choice = Choice.objects.get(pk=choice_id)
                choice_answer = ChoiceAnswer.objects.create(response=form_response, formfield_id=field_id, value=choice.text)
                saved_responses.append(choice_answer)

            elif field_type == FormType.MULTIPLE_CHOICE:
                if isinstance(field_value, list):
                    for choice_id in field_value:
                        choice = Choice.objects.get(pk=choice_id)
                        choice_answer = ChoiceAnswer.objects.create(response=form_response, formfield_id=field_id, value=choice.text)
                        saved_responses.append(choice_answer)
                else:  # It's a string
                    choice = Choice.objects.get(pk=field_value)
                    choice_answer = ChoiceAnswer.objects.create(response=form_response, formfield_id=field_id, value=choice.text)
                    saved_responses.append(choice_answer)

            elif field_type == FormType.FILE_UPLOAD:
                file_answer = FileTable.objects.create(response=form_response, formfield_id=field_id, value=field_value)
                saved_responses.append(file_answer)

            elif field_type == FormType.DATE:
                date_answer = DateTable.objects.create(response=form_response, formfield_id=field_id, value=field_value)
                saved_responses.append(date_answer)

            elif field_type == FormType.CHECKBOX:
                checkbox_answer = CheckBox.objects.create(response=form_response, formfield_id=field_id, value=field_value)
                saved_responses.append(checkbox_answer)

            elif field_type == FormType.SHORT_ANSWER:
                short_answer = ShortAnswer.objects.create(response=form_response, formfield_id=field_id, value=field_value)
                saved_responses.append(short_answer)

            elif field_type == FormType.LONG_ANSWER:
                long_answer = LongAnswer.objects.create(response=form_response, formfield_id=field_id, value=field_value)
                saved_responses.append(long_answer)

        return saved_responses





class FormFieldValueSerializer(serializers.ModelSerializer):
    value = serializers.SerializerMethodField()

    class Meta:
        model = FormField
        exclude = ['form']
        
    def get_value(self, instance):
        form_response = self.context.get('form_response')
        
        field_type = instance.type
        
        if field_type == FormType.SHORT_ANSWER:
            try:
                short_answer = ShortAnswer.objects.get(formfield=instance, response=form_response)
                return short_answer.value
            except ShortAnswer.DoesNotExist:
                return None
        
        elif field_type == FormType.LONG_ANSWER:
            try:
                long_answer = LongAnswer.objects.get(formfield=instance, response=form_response)
                return long_answer.value
            except LongAnswer.DoesNotExist:
                return None
        
        elif field_type in [FormType.RADIO_BUTTON,FormType.MULTIPLE_CHOICE,FormType.DROPDOWN]:
            choices = ChoiceAnswer.objects.filter(formfield=instance, response=form_response)
            return [choice.text for choice in choices]
        
        elif field_type == FormType.CHECKBOX:
            try:
                checkbox = CheckBox.objects.get(formfield=instance, response=form_response)
                return checkbox.value
            except CheckBox.DoesNotExist:
                return None
       
        elif field_type == FormType.DATE:
            try:
                date = DateTable.objects.get(formfield=instance, response=form_response)
                return date.value
            except DateTable.DoesNotExist:
                return None
       
        elif field_type == FormType.FILE_UPLOAD:
            try:
                file = FileTable.objects.get(formfield=instance, response=form_response)
                return file.value
            except FileTable.DoesNotExist:
                return None
        
        else:
            return None
        
        
        
class FormResponseSerializer(serializers.ModelSerializer):
    form_fields = FormFieldValueSerializer(many=True,source='form.form_fields')

    class Meta:
        model = FormResponse
        fields = '__all__'
        
    def to_representation(self, instance):
        form_fields_serializer = FormFieldValueSerializer(
            instance.form.form_fields.all(), 
            many=True, 
            context={'form_response': instance}
        )
        form_fields_data = form_fields_serializer.data
        
        response_data = super().to_representation(instance)
        response_data['form_fields'] = form_fields_data
        
        return response_data