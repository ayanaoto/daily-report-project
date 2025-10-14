# reports/forms.py
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
    RequiredMaterial, # 新しいモデルをインポート
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
        fields = ['company_name', 'contact_person', 'phone_number', 'email_address', 'account_manager']

# ===== 案件 =====
class DealForm(forms.ModelForm):
    class Meta:
        model = Deal
        fields = ['deal_name', 'customer', 'status', 'amount', 'close_date']

# ===== 日報 =====
class ReportForm(forms.ModelForm):
    hours = forms.IntegerField(label="作業時間（時）", required=False, min_value=0, initial=0, widget=forms.NumberInput(attrs={"class": "form-control"}))
    minutes = forms.IntegerField(label="作業時間（分）", required=False, min_value=0, max_value=59, initial=0, widget=forms.NumberInput(attrs={"class": "form-control", "step": 5}))
    
    class Meta:
        model = Report
        fields = ["location", "progress", "content", "remarks"]
        widgets = {
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'progress': forms.Select(attrs={'class': 'form-select'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': '例: 〇〇、△△が必要'}),
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
        fields = ["title", "description", "deal", "assignee", "is_done"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "deal": forms.Select(attrs={"class": "form-select"}),
            "assignee": forms.Select(attrs={"class": "form-select"}),
            "is_done": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

# ▼▼▼【ここから追加】▼▼▼
# ===== 必要物リスト =====
class RequiredMaterialForm(forms.ModelForm):
    class Meta:
        model = RequiredMaterial
        # フォームでユーザーに入力させるフィールド
        fields = ['name', 'quantity']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '物品名'}),
            'quantity': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '数量（例: 1）'}),
        }
# ▲▲▲【ここまで】▲▲▲