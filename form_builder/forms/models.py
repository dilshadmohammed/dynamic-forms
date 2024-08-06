import uuid
from django.db import models
from utils.types import FormType
from user.models import User

class Form(models.Model):
    id = models.CharField(primary_key=True, max_length=36, default=uuid.uuid4)
    user = models.ForeignKey(User, related_name='forms', on_delete=models.CASCADE)
    title = models.CharField(max_length=255, default='Untitled-form')
    description = models.TextField(null=True, blank=True)

class FormField(models.Model):
    id = models.CharField(primary_key=True, max_length=36, default=uuid.uuid4)
    form = models.ForeignKey(Form, related_name='form_fields', on_delete=models.CASCADE)
    type = models.CharField(max_length=20, choices=FormType.CHOICES, default=FormType.SHORT_ANSWER)
    label = models.TextField(null=True, blank=True)
    is_required = models.BooleanField()

class FormResponse(models.Model):
    id = models.CharField(primary_key=True, max_length=36, default=uuid.uuid4)
    form = models.ForeignKey(Form, related_name='responses', on_delete=models.CASCADE)

class Choice(models.Model):
    id = models.CharField(primary_key=True, max_length=36, default=uuid.uuid4)
    formfield = models.ForeignKey(FormField, related_name='choices', on_delete=models.CASCADE)
    text = models.CharField(max_length=255)
    
class PaymentRequest(models.Model):
    id = models.CharField(primary_key=True, max_length=36, default=uuid.uuid4)
    formfield = models.ForeignKey(FormField, related_name='payment_details', on_delete=models.CASCADE)
    upi_id = models.CharField(max_length=100,null=False,blank=True)
    amount = models.IntegerField(default=0)

class ChoiceAnswer(models.Model):
    id = models.CharField(primary_key=True, max_length=36, default=uuid.uuid4)
    response = models.ForeignKey(FormResponse, related_name='choice_answers', on_delete=models.CASCADE)
    formfield = models.ForeignKey(FormField, related_name='choice_answers', on_delete=models.CASCADE)
    value = models.CharField(max_length=255)

class LongAnswer(models.Model):
    id = models.CharField(primary_key=True, max_length=36, default=uuid.uuid4)
    response = models.ForeignKey(FormResponse, related_name='long_answers', on_delete=models.CASCADE)
    formfield = models.ForeignKey(FormField, related_name='long_answers', on_delete=models.CASCADE)
    value = models.TextField()

class ShortAnswer(models.Model):
    id = models.CharField(primary_key=True, max_length=36, default=uuid.uuid4)
    response = models.ForeignKey(FormResponse, related_name='short_answers', on_delete=models.CASCADE)
    formfield = models.ForeignKey(FormField, related_name='short_answers', on_delete=models.CASCADE)
    value = models.CharField(max_length=255)

class CheckBox(models.Model):
    id = models.CharField(primary_key=True, max_length=36, default=uuid.uuid4)
    response = models.ForeignKey(FormResponse, related_name='checkboxes', on_delete=models.CASCADE)
    formfield = models.ForeignKey(FormField, related_name='checkboxes', on_delete=models.CASCADE)
    value = models.BooleanField(default=False)

class DateTable(models.Model):
    id = models.CharField(primary_key=True, max_length=36, default=uuid.uuid4)
    response = models.ForeignKey(FormResponse, related_name='dates', on_delete=models.CASCADE)
    formfield = models.ForeignKey(FormField, related_name='dates', on_delete=models.CASCADE)
    value = models.DateField()

class FileTable(models.Model):
    id = models.CharField(primary_key=True, max_length=36, default=uuid.uuid4)
    response = models.ForeignKey(FormResponse, related_name='files', on_delete=models.CASCADE)
    formfield = models.ForeignKey(FormField, related_name='files', on_delete=models.CASCADE)
    value = models.FileField(upload_to='formfiles/')
