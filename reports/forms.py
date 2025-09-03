# reports/forms.py

from django import forms
from .models import Report, Customer, WorkLog, Deal, TroubleshootingReport # ★ TroubleshootingReport を追加

class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ['customer', 'title', 'content']
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
        }

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['customer_name', 'account_manager']
        widgets = {
            'customer_name': forms.TextInput(attrs={'class': 'form-control'}),
            'account_manager': forms.Select(attrs={'class': 'form-control'}),
        }

class WorkLogForm(forms.ModelForm):
    hours = forms.IntegerField(label="作業時間（時）", required=False, min_value=0, widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '例: 2'}))
    minutes = forms.IntegerField(label="作業時間（分）", required=False, min_value=0, max_value=59, widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '例: 30'}))

    class Meta:
        model = WorkLog
        fields = ['customer', 'deal', 'work_date', 'hours', 'minutes', 'progress_status', 'repair_needed', 'remarks', 'attachment']
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-control', 'id': 'id_customer'}),
            'deal': forms.Select(attrs={'class': 'form-control', 'id': 'id_deal'}),
            'work_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'progress_status': forms.Select(attrs={'class': 'form-control'}),
            'repair_needed': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'attachment': forms.FileInput(attrs={'class': 'form-control'}),
        }


# ★★★ ここからが追記箇所 ★★★
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