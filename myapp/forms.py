from dataclasses import fields
from pyexpat import model
from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.core.exceptions import ValidationError
from django.db import transaction
from .models import Employee, Leave, User
import numpy as np 

from django.contrib.admin.widgets import AdminDateWidget
 
class UserCreationForm(forms.ModelForm):
   password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
   password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput)
 
   class Meta:
       model = User
       fields = ('email',)
 
   def clean_password2(self):
       # Check that the two password entries match
       password1 = self.cleaned_data.get("password1")
       password2 = self.cleaned_data.get("password2")
       if password1 and password2 and password1 != password2:
           raise ValidationError("Passwords don't match")
       return password2
 
   def save(self, commit=True):
       # Save the provided password in hashed format
       user = super().save(commit=False)
       user.set_password(self.cleaned_data["password1"])
       if commit:
           user.save()
       return user

class SignUp(forms.ModelForm):
    pass

class LeaveRequestForm(forms.ModelForm):
    #from_date=forms.DateField(widget = forms.SelectDateWidget())
    #to_date=forms.DateField(widget = forms.SelectDateWidget())

    # from_date=forms.DateField(input_formats=['%d/%m/%Y'],
    #     widget=forms.DateTimeInput(attrs={
    #         'class': 'form-control datetimepicker-input',
    #         'data-target': '#datetimepicker1'
    #     }))
    # to_date=forms.DateField(widget = AdminDateWidget())

    class Meta:
        model=Leave
        exclude=['id','employee','is_leave_approved','status','is_leave_rejected','is_leave_cancelled','is_leave_pending']
    def clean(self):
        cleaned_data = super().clean()
        from_date=cleaned_data.get("from_date")
        to_date=cleaned_data.get("to_date")
        print(from_date)
        print(to_date)
        if(from_date>=to_date):
            raise ValidationError(
                "From Date can Not be After To Date"
            )
    @transaction.atomic
    def save(self,current_user):
        leave_request=super().save(commit=False)
        leave_request.employee=Employee.objects.get(user=current_user)
        leave_request.save()
        return leave_request

class GrantLeaveRequestForm(forms.ModelForm):
    employee_id = forms.CharField(max_length=50,disabled=True,required=False)
    max_leaves = forms.IntegerField(disabled=True,required=False)
    leaves_remaining = forms.IntegerField(disabled=True,required=False)
    from_date = forms.DateTimeField(disabled=True,required=False)
    to_date = forms.DateTimeField(disabled=True,required=False)
    reason = forms.CharField(disabled=True,required=False)
    Status_Choices=[
    ('Approved','Approved'),
    ('Rejected','Rejected'),
    ]
    status=forms.ChoiceField(choices=Status_Choices)
    def __init__(self,*args, **kwargs):
            #self.default_text = kwargs.pop('text')

        super(GrantLeaveRequestForm, self).__init__(*args, **kwargs)
        leave=self.instance
        if leave.is_leave_pending and leave.is_leave_approved and leave.is_leave_cancelled:
            Status_Choices=[('Cancelation Approved','Cancelation Approved'),
    ('Cancelation Rejected','Cancelation Rejected'),
    ('Cancelation Pending','Cancelation Pending'),
    
    ]
        if leave.is_leave_pending and leave.is_leave_approved:
            Status_Choices=[('Approved','Approved'),
    ('Rejected','Rejected'),
    ]
        if not leave.is_leave_pending and leave.is_leave_approved or  leave.is_leave_rejected and not leave.is_leave_cancelled:
            Status_Choices=[('Approved','Approved'),
    ('Rejected','Rejected'),
    ]
        if not leave.is_leave_pending and leave.is_leave_approved and leave.is_leave_cancelled and leave.is_leave_rejected:
            Status_Choices=[('Cancelation Approved','Cancelation Approved'),
    ('Cancelation Rejected','Cancelation Rejected'),
    ('Cancelation Pending','Cancelation Pending'),
    
    ]
        if leave.is_leave_approved:
            Status_Choices=[('Pending','Pending'),
        ('Approved','Approved'),
        ('Cancelation Approved','Cancelation Approved'),
        ('Cancelation Rejected','Cancelation Rejected'),
        
            ]
        else:
            Status_Choices=[('Pending','Pending'),
        ('Approved','Approved'),
        ('Rejected','Rejected'),
        ('Cancelation Approved','Cancelation Approved'),
        ('Cancelation Rejected','Cancelation Rejected'),
        ('Cancelation Pending','Cancelation Pending'),
        ]
        self.fields['status'].choices = Status_Choices
    class Meta:
        model=Leave
        fields=['from_date','to_date','status','reason']
    def save(self,leave_request):
        print("-------------------------------------------")
        print(self.cleaned_data['status']=='Approved')
        #if line manager sent True as leave approved
        if self.cleaned_data['status']=='Approved':
            employee=leave_request.employee
            business_days_count=np.busday_count(leave_request.from_date.strftime('%Y-%m-%d'),leave_request.to_date.strftime('%Y-%m-%d'))
                    
            if leave_request.status == 'Rejected':
                employee.leaves_remaining =employee.leaves_remaining - business_days_count
                leave_request.is_leave_approved=True
                leave_request.status='Approved'
                leave_request.save()
                employee.save()
                
            if leave_request.status == 'Pending':
                employee.leaves_remaining =employee.leaves_remaining - business_days_count
                leave_request.is_leave_approved=True
                leave_request.status='Approved'
                leave_request.save()
                employee.save()
        #Now New Form data Status is Set At Rejected    
        elif self.cleaned_data['status']=='Rejected':
            employee=leave_request.employee
            business_days_count=np.busday_count(leave_request.from_date.strftime('%Y-%m-%d'),leave_request.to_date.strftime('%Y-%m-%d'))
                  
            if leave_request.status == 'Pending':
                leave_request.is_leave_approved=False
                leave_request.status='Rejected'
                leave_request.save()
                
            if leave_request.status == 'Approved':
                employee.leaves_remaining =employee.leaves_remaining + business_days_count
                leave_request.is_leave_approved=False
                leave_request.status='Rejected'
                leave_request.save()
                employee.save()
        return leave_request

class GrantLeaveRequestModelForm(forms.ModelForm):
    employee_id = forms.CharField(max_length=50,disabled=True)
    max_leaves = forms.IntegerField(disabled=True)
    leaves_remaining = forms.IntegerField(disabled=True)
    class Meta:
        model=Leave
        exclude=["employee"]


# ---------------------------------------Cancellation request by user--------------------------------------- 

class CancelLeaveRequestForm(forms.Form):
    from_date = forms.DateField(disabled=True,required=False)
    to_date = forms.DateField(disabled=True,required=False)
    cancellation_reason = forms.CharField(required=True)

    def save(self,leave_request):
        if leave_request.is_leave_approved:
            leave_request.is_leave_cancelled = True
            leave_request.is_leave_pending = True
            temp = leave_request.reason
            temp += self.cleaned_data['cancellation_reason']
            leave_request.reason =  temp

            leave_request.status='Cancelation Pending'
            leave_request.save()

        return leave_request
        

        




