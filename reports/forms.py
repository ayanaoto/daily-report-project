from django import forms
from .models import Report, Customer, TroubleshootingReport

class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = [
            'customer_name',
            'deal_name',
            'work_date',
            'progress_status',
            'work_hours',
            'work_details',
            'remarks',
            'attachment',
        ]
        widgets = {
            'customer_name': forms.TextInput(attrs={'class': 'form-control'}),
            'deal_name': forms.TextInput(attrs={'class': 'form-control'}),
            'work_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'progress_status': forms.Select(attrs={'class': 'form-control'}),
            'work_hours': forms.TextInput(attrs={'class': 'form-control'}),
            'work_details': forms.Textarea(attrs={'class': 'form-control', 'rows': 10}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'attachment': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['customer_name', 'account_manager']
        widgets = {
            'customer_name': forms.TextInput(attrs={'class': 'form-control'}),
            'account_manager': forms.Select(attrs={'class': 'form-control'}),
        }

class TroubleshootingReportForm(forms.ModelForm):
    class Meta:
        model = TroubleshootingReport
        fields = ['title', 'location', 'symptom', 'solution', 'keywords']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'symptom': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'solution': forms.Textarea(attrs={'class': 'form-control', 'rows': 6}),
            'keywords': forms.TextInput(attrs={'class': 'form-control'}),
        }
