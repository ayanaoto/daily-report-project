# reports/forms.py (全文)
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import (
    Profile,
    Customer,
    Deal,
    Report,
    Troubleshooting,
    RequiredItem,
    VoiceLog,
)

# ===== プロフィール =====
class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["background_image"]

# ===== サインアップ =====
class SignUpForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        fields = ("username", "email")

# ===== 顧客 =====
class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['company_name', 'contact_name', 'phone_number', 'email', 'account_manager']
        # 【追加】各フィールドにCSSクラスを指定
        widgets = {
            'company_name': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'account_manager': forms.Select(attrs={'class': 'form-select'}),
        }

# ===== 案件 =====
class DealForm(forms.ModelForm):
    class Meta:
        model = Deal
        fields = ['name', 'customer', 'status', 'amount', 'expected_order_date']

# ===== 日報 =====
class ReportForm(forms.ModelForm):
    hours = forms.IntegerField(label="作業時間（時）", required=False, min_value=0, initial=0, widget=forms.NumberInput(attrs={"class": "form-control"}))
    minutes = forms.IntegerField(label="作業時間（分）", required=False, min_value=0, max_value=59, initial=0, widget=forms.NumberInput(attrs={"class": "form-control", "step": 5}))
    
    class Meta:
        model = Report
        fields = ["title", "location", "progress", "work_content", "note"]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'progress': forms.Select(attrs={'class': 'form-select'}),
            'work_content': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

# ===== ナレッジ（トラブルシュート） =====
class TroubleshootingForm(forms.ModelForm):
    class Meta:
        model = Troubleshooting
        exclude = ('author',)

# ===== ToDo =====
class RequiredItemForm(forms.ModelForm):
    class Meta:
        model = RequiredItem
        fields = ["title", "assignee", "required_items_list", "is_done"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "assignee": forms.Select(attrs={"class": "form-select"}),
            "required_items_list": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "is_done": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }