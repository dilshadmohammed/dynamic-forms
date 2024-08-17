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
    order = models.PositiveIntegerField(null=True, blank=True)
    
    class Meta:
        ordering = ['order']
    
    def save(self, *args, **kwargs):
        
        if self._state.adding:  # New instance
            if self.order is None:
                max_order = FormField.objects.filter(form=self.form).aggregate(max_order=models.Max('order'))['max_order']
                if max_order is not None:
                    self.order = max_order + 1
                else:
                    self.order = 0
        else:  # Existing instance
            current_order = FormField.objects.get(pk=self.pk).order
            if self.order != current_order:
                if self.order < current_order:
                    # Move up: increment order of fields between new and old position
                    FormField.objects.filter(
                        form=self.form,
                        order__gte=self.order,
                        order__lt=current_order
                    ).exclude(pk=self.pk).update(order=models.F('order') + 1)
                else:
                    # Move down: decrement order of fields between old and new position
                    FormField.objects.filter(
                        form=self.form,
                        order__gt=current_order,
                        order__lte=self.order
                    ).exclude(pk=self.pk).update(order=models.F('order') - 1)
        
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Decrement order of all fields that come after the deleted order
        FormField.objects.filter(
            form=self.form,
            order__gt=self.order
        ).update(order=models.F('order') - 1)
        super().delete(*args, **kwargs)


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
    qr_code = models.ImageField(upload_to='upi_qrcode/',null=True)
    
    def __str__(self):
        return self.upi_id

class Payment(models.Model):
    id = models.CharField(primary_key=True, max_length=36, default=uuid.uuid4)
    formfield = models.ForeignKey(FormField, related_name='payments_paid', on_delete=models.SET_NULL,null=True)
    response = models.ForeignKey(FormResponse, related_name='payments_paid', on_delete=models.SET_NULL,null=True)
    value = models.ImageField(upload_to='payment_proofs/')
    
    def __str__(self):
        return str(self.id)

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
