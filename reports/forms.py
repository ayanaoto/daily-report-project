from django import forms
from .models import Report, Customer, TroubleshootingReport

class ReportForm(forms.ModelForm):
    # 時間と分を簡単に入力するためのフィールドを追加
    hours = forms.IntegerField(label="作業時間（時）", required=False, min_value=0, widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '例: 2'}))
    minutes = forms.IntegerField(label="作業時間（分）", required=False, min_value=0, max_value=59, widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '例: 30'}))

    class Meta:
        model = Report
        fields = [
            'customer_name', 'deal_name', 'work_date', 'progress_status',
            'hours', 'minutes', 'work_details', 'remarks', 'attachment'
        ]
        widgets = {
            'customer_name': forms.TextInput(attrs={'class': 'form-control'}),
            'deal_name': forms.TextInput(attrs={'class': 'form-control'}),
            'work_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'progress_status': forms.Select(attrs={'class': 'form-control'}), # プルダウン
            'work_details': forms.Textarea(attrs={'class': 'form-control', 'rows': 10}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'attachment': forms.FileInput(attrs={'class': 'form-control'}),
        }

# ... (CustomerForm と TroubleshootingReportForm は変更なし) ...
class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['customer_name', 'account_manager']
        widgets = { 'customer_name': forms.TextInput(attrs={'class': 'form-control'}), 'account_manager': forms.Select(attrs={'class': 'form-control'})}

class TroubleshootingReportForm(forms.ModelForm):
    class Meta:
        model = TroubleshootingReport
        fields = ['title', 'location', 'work_details', 'symptom', 'solution', 'keywords']
        widgets = {'title': forms.TextInput(attrs={'class': 'form-control'}), 'location': forms.TextInput(attrs={'class': 'form-control'}), 'work_details': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}), 'symptom': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}), 'solution': forms.Textarea(attrs={'class': 'form-control', 'rows': 6}), 'keywords': forms.TextInput(attrs={'class': 'form-control'})}