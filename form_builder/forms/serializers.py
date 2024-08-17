from rest_framework import serializers
from datetime import datetime
from django.core.files.uploadedfile import UploadedFile
from user.models import User
from .models import Form,FormField,FormResponse,Choice,ChoiceAnswer,LongAnswer,ShortAnswer,CheckBox,DateTable,FileTable,PaymentRequest,Payment
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
    qr_code = serializers.ImageField(required=False,write_only=True)
    
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
                representation['qr_code'] = payment_details.qr_code.url
            else:
                representation['upi_id'] = None
                representation['amount'] = 0
                representation['qr_code'] = None
        return representation
    

    def create(self, validated_data):
        form = self.context['form']
        choices_data = validated_data.pop('choices', None)
        upi_id = validated_data.pop('upi_id',None)
        amount = validated_data.pop('amount',None)
        qr_code = validated_data.pop('qr_code',None)
        if 'is_required' not in validated_data:
            validated_data['is_required'] = False
        form_field = FormField.objects.create(form=form, **validated_data)
        if choices_data and validated_data['type'] in [FormType.RADIO_BUTTON,FormType.MULTIPLE_CHOICE,FormType.DROPDOWN]:
            for choice_data in choices_data:
                Choice.objects.create(formfield=form_field, text=choice_data)
        if validated_data['type'] == FormType.UPI_PAYMENT and upi_id and amount and qr_code:
            PaymentRequest.objects.create(formfield=form_field, upi_id=upi_id, amount=amount, qr_code=qr_code)

            
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
        elif instance.type == FormType.UPI_PAYMENT:
            if upi_id and amount and qr_code:
                PaymentRequest.objects.update_or_create(
                    formfield=instance,
                    defaults={'upi_id': upi_id, 'amount': amount, 'qr_code': qr_code}
                )
            elif instance.payment_details.exists():
                instance.payment_details.all().delete()
        return instance
        
        
    
class FormDetailSerializer(serializers.ModelSerializer):
    form_fields = FormFieldSerializer(many=True)
    
    class Meta:
        model=Form
        exclude=['user']
    
    

class FormResponseValueSerializer(serializers.Serializer):
    value = serializers.JSONField(required=True)

    # def validate(self,data):
    #     print(data)
    #     return data
    # def to_internal_value(self, data):
    #     """
    #     Override to enforce that input data must be a dictionary with a 'value' key.
    #     """
    #     print('hello')
    #     if not isinstance(data, dict):
    #         raise serializers.ValidationError("Expected a dictionary for form field response.")
    #     if 'value' not in data:
    #         raise serializers.ValidationError("Field 'value' is required.")
    #     return super().to_internal_value(data)

class FormSubmissionSerializer(serializers.Serializer):
    form = serializers.CharField(required=True)
    form_fields = serializers.DictField(required=True)
    
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

        for field_id in form_field_ids:
            if field_id in required_field_ids and field_id not in form_fields_response:
                raise serializers.ValidationError(f"Required field '{required_field_ids[field_id]}' is missing.")
        for field_id, field_value in form_fields_response.items():
            if field_id not in form_field_ids:
                raise serializers.ValidationError(f"Form field with ID '{field_id}' does not exist.")
            
            field_type = form_field_ids[field_id]

            if field_type in [FormType.RADIO_BUTTON, FormType.DROPDOWN]:
                if not isinstance(field_value, str):
                    raise serializers.ValidationError(f"Invalid value type for choice field with ID '{field_id}'.")
                if not Choice.objects.filter(id=field_value, formfield_id=field_id).exists():
                    raise serializers.ValidationError(f"Choice with ID '{field_value}' does not exist for field with ID '{field_id}'.")

            elif field_type == FormType.MULTIPLE_CHOICE:
                if not isinstance(field_value, (list, str)):
                    raise serializers.ValidationError(f"Invalid value type for multiple choice field with ID '{field_id}'. Expected a list or string.")
                if isinstance(field_value, list):
                    for choice_id in field_value:
                        if not Choice.objects.filter(id=choice_id, formfield_id=field_id).exists():
                            raise serializers.ValidationError(f"Choice with ID '{choice_id}' does not exist for field with ID '{field_id}'.")
                else:  # It's a string
                    if not Choice.objects.filter(id=field_value, formfield_id=field_id).exists():
                        raise serializers.ValidationError(f"Choice with ID '{field_value}' does not exist for field with ID '{field_id}'.")

            elif field_type == FormType.FILE_UPLOAD:
                if not isinstance(field_value, UploadedFile):  # Assuming file value is stored as a URL or path
                    raise serializers.ValidationError(f"Invalid value type for file field with ID '{field_id}'.")

            elif field_type == FormType.DATE:
                try:
                    datetime.strptime(field_value, '%d-%m-%Y')  # Try 'dd-mm-yyyy' format
                except ValueError:
                    try:
                        datetime.strptime(field_value, '%d/%m/%Y')  # Try 'dd/mm/yyyy' format
                    except ValueError:
                        try:
                            datetime.strptime(field_value, '%Y-%m-%d')  # Try 'yyyy-mm-dd' format
                        except ValueError:
                            raise serializers.ValidationError(f"Invalid date format for date field with ID '{field_id}'. Expected format is 'DD-MM-YYYY', 'DD/MM/YYYY', or 'YYYY-MM-DD'.")
            
            elif field_type == FormType.CHECKBOX:
                if not isinstance(field_value, bool):  # Expecting a boolean value
                    raise serializers.ValidationError(f"Invalid value type for checkbox field with ID '{field_id}'. Expected a boolean.")

            elif field_type in [FormType.SHORT_ANSWER, FormType.LONG_ANSWER]:
                if not isinstance(field_value, str):
                    raise serializers.ValidationError(f"Invalid value type for short answer field with ID '{field_id}'.")

            elif field_type == FormType.UPI_PAYMENT:
                if not isinstance(field_value, UploadedFile):  # Assuming UPI payment info is stored as a string
                    raise serializers.ValidationError(f"Invalid value type for UPI payment field with ID '{field_id}'.")
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

        for field_id, field_value in self.validated_data['form_fields'].items():
            field_type = form_fields.get(id=field_id).type

            if field_type == FormType.RADIO_BUTTON or field_type == FormType.DROPDOWN:
                choice = Choice.objects.get(pk=field_value)
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
                saved_responses.append(file_answer.value.url if file_answer.value else None)

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

            elif field_type == FormType.UPI_PAYMENT:
                payment = Payment.objects.create(response=form_response, formfield_id=field_id, value=field_value)
                saved_responses.append(payment.value.url if payment.value else None)
        return saved_responses
    
        
        
        
# class FormResponseSerializer(serializers.ModelSerializer):
#     form_fields = FormResponseValueSerializer(many=True,source='form.form_fields')

#     class Meta:
#         model = FormResponse
#         fields = '__all__'
        
#     def to_representation(self, instance):
#         form_fields_serializer = FormResponseValueSerializer(
#             instance.form.form_fields.all(), 
#             many=True, 
#             context={'form_response': instance}
#         )
#         form_fields_data = form_fields_serializer.data
        
#         response_data = super().to_representation(instance)
#         response_data['form_fields'] = form_fields_data
        
#         return response_data


class FormResponseSerializer(serializers.ModelSerializer):
    form_fields = serializers.SerializerMethodField()

    class Meta:
        model = FormResponse
        fields = '__all__'
    
    def get_form_fields(self, instance):
        """
        Customize the representation of form_fields to be a dictionary.
        """
        form_fields_list = []
        form_fields = instance.form.form_fields.all()
        for field in form_fields:
            field_value = self.get_field_value(instance, field)
            form_fields_list.append((field.type,field_value))
        return form_fields_list

    def get_field_value(self, instance, field):
        """
        Get the value of a form field response for the given instance.
        """
        if field.type == FormType.SHORT_ANSWER:
            value = ShortAnswer.objects.filter(response=instance, formfield=field).first()
        elif field.type == FormType.LONG_ANSWER:
            value = LongAnswer.objects.filter(response=instance, formfield=field).first()
        elif field.type in [FormType.DROPDOWN,FormType.MULTIPLE_CHOICE,FormType.RADIO_BUTTON]:
            value = ChoiceAnswer.objects.filter(response=instance, formfield=field).first()
        elif field.type == FormType.CHECKBOX:
            value = CheckBox.objects.filter(response=instance, formfield=field).first()
        elif field.type == FormType.DATE:
            value = DateTable.objects.filter(response=instance, formfield=field).first()
        elif field.type == FormType.FILE_UPLOAD:
            value = FileTable.objects.filter(response=instance, formfield=field).first()
            return value.value.url if value and value.value else None
        elif field.type == FormType.UPI_PAYMENT:
            value = Payment.objects.filter(response=instance, formfield=field).first()
            return value.value.url if value and value.value else None
        else:
            value = None
        return value.value if value else None

    def to_representation(self, instance):
        """
        Convert the instance to a dictionary representation, including form_fields.
        """
        response_data = super().to_representation(instance)
        response_data['form_fields'] = self.get_form_fields(instance)
        return response_data