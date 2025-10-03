from __future__ import annotations

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.forms import inlineformset_factory

from .models import (
    Profile,
    Customer,
    Deal,
    Report,
    Troubleshooting,
    RequiredItem,
    ReportAttachment,
    VoiceLog,  # ★ 追加
)


# ===== プロフィール =====
class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["background_image"]
        widgets = {
            "background_image": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }


# ===== サインアップ =====
class SignUpForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("username",)
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ("password1", "password2"):
            if name in self.fields:
                self.fields[name].widget.attrs.update({"class": "form-control"})


# ===== 顧客 =====
class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = [
            "company_name",
            "contact_person",
            "phone_number",
            "email_address",
            "account_manager",
        ]
        widgets = {
            "company_name": forms.TextInput(attrs={"class": "form-control"}),
            "contact_person": forms.TextInput(attrs={"class": "form-control"}),
            "phone_number": forms.TextInput(attrs={"class": "form-control"}),
            "email_address": forms.EmailInput(attrs={"class": "form-control"}),
            "account_manager": forms.Select(attrs={"class": "form-select"}),
        }


# ===== 案件 =====
class DealForm(forms.ModelForm):
    class Meta:
        model = Deal
        fields = ["deal_name", "customer", "status", "amount", "close_date"]
        widgets = {
            "deal_name": forms.TextInput(attrs={"class": "form-control"}),
            "customer": forms.Select(attrs={"class": "form-select"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "amount": forms.NumberInput(attrs={"class": "form-control", "step": 1, "min": 0}),
            "close_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
        }


# ===== 日報 =====
class ReportForm(forms.ModelForm):
    # 所要時間を UI で時分入力
    hours = forms.IntegerField(
        required=False, min_value=0, max_value=24, initial=0,
        widget=forms.NumberInput(attrs={"class": "form-control"})
    )
    minutes = forms.IntegerField(
        required=False, min_value=0, max_value=59, initial=0,
        widget=forms.NumberInput(attrs={"class": "form-control", "step": 5})
    )

    class Meta:
        model = Report
        fields = [
            "location", "progress", "content", "remarks",
        ]
        widgets = {
            "location": forms.TextInput(attrs={"class": "form-control"}),
            "progress": forms.Select(attrs={"class": "form-select"}),
            "content": forms.Textarea(attrs={"class": "form-control", "rows": 6}),
            "remarks": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # モデルに無いフィールドが混ざっていたら除外（安全側）
        model_field_names = {f.name for f in Report._meta.get_fields()}
        for fname in list(self.fields.keys()):
            if fname not in ("hours", "minutes") and fname not in model_field_names:
                self.fields.pop(fname, None)

        # Bootstrap クラスの補強
        for f in self.fields.values():
            if isinstance(f.widget, (forms.TextInput, forms.EmailInput, forms.NumberInput, forms.DateInput, forms.TimeInput, forms.Textarea)):
                f.widget.attrs.setdefault("class", "form-control")
            elif isinstance(f.widget, (forms.Select, forms.SelectMultiple)):
                f.widget.attrs.setdefault("class", "form-select")

    def clean(self):
        cleaned = super().clean()
        h = cleaned.get("hours") or 0
        m = cleaned.get("minutes") or 0
        if h < 0:
            cleaned["hours"] = 0
        if m < 0:
            cleaned["minutes"] = 0
        return cleaned


# ===== ナレッジ（トラブルシュート） =====
class TroubleshootingForm(forms.ModelForm):
    class Meta:
        model = Troubleshooting
        fields = ["title", "location", "symptom", "solution", "keywords", "occurred_at"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "location": forms.TextInput(attrs={"class": "form-control"}),
            "symptom": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "solution": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "keywords": forms.TextInput(attrs={"class": "form-control"}),
            "occurred_at": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
        }


# ===== ToDo（RequiredItem） =====
class RequiredItemForm(forms.ModelForm):
    class Meta:
        model = RequiredItem
        fields = ["title", "deal", "is_done"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "deal": forms.Select(attrs={"class": "form-select"}),
            "is_done": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


# ===== 添付ファイル =====
class ReportAttachmentForm(forms.ModelForm):
    class Meta:
        model = ReportAttachment
        fields = ["file", "title"]
        widgets = {
            "file": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "任意のタイトル"}),
        }


# Report と添付のインラインフォームセット
ReportAttachmentFormSet = inlineformset_factory(
    parent_model=Report,
    model=ReportAttachment,
    form=ReportAttachmentForm,
    extra=3,
    can_delete=True,
)

# ===== ▼ 追加：音声アップロード用フォーム（API内部で任意利用） =====
class VoiceLogUploadForm(forms.ModelForm):
    class Meta:
        model = VoiceLog
        fields = ["audio_file", "text", "intent", "ts", "lat", "lon", "amount", "customer", "when"]
        widgets = {
            "audio_file": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }
