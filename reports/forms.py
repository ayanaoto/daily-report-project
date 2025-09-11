from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Report, Customer, Deal, Troubleshooting, RequiredItem, Profile

class SignUpForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        fields = ('username', 'email')

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['background_image']

class ReportForm(forms.ModelForm):
    hours = forms.IntegerField(label="作業時間（時）", min_value=0, required=False, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    minutes = forms.IntegerField(label="作業時間（分）", min_value=0, max_value=59, required=False, widget=forms.NumberInput(attrs={'class': 'form-control'}))

    class Meta:
        model = Report
        fields = ['location', 'progress', 'content', 'remarks']
        widgets = {
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'progress': forms.Select(attrs={'class': 'form-select'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['company_name', 'contact_person', 'phone_number', 'email_address', 'account_manager']

class DealForm(forms.ModelForm):
    class Meta:
        model = Deal
        fields = ['deal_name', 'customer', 'status', 'amount', 'close_date']

class TroubleshootingForm(forms.ModelForm):
    class Meta:
        model = Troubleshooting
        fields = ['title', 'location', 'symptom', 'solution', 'keywords', 'occurred_at']

class RequiredItemForm(forms.ModelForm):
    class Meta:
        model = RequiredItem
        fields = ['title', 'deal', 'is_done']