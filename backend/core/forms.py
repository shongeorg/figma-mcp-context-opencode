from __future__ import annotations

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.exceptions import ValidationError

from .models import Address, User


class RegisterForm(UserCreationForm):
    first_name = forms.CharField(max_length=150, widget=forms.TextInput(
        attrs={"class": "input", "placeholder": "First name", "autocomplete": "given-name"},
    ))
    last_name = forms.CharField(max_length=150, required=False, widget=forms.TextInput(
        attrs={"class": "input", "placeholder": "Last name", "autocomplete": "family-name"},
    ))
    email = forms.EmailField(widget=forms.EmailInput(
        attrs={"class": "input", "placeholder": "Email", "autocomplete": "email"},
    ))
    phone = forms.CharField(label="Phone (optional)", max_length=32, required=False,
                            widget=forms.TextInput(
        attrs={"class": "input", "placeholder": "Phone (optional)", "autocomplete": "tel"},
    ))

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "first_name", "last_name", "email", "phone")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update({
            "class": "input", "placeholder": "Username", "autocomplete": "username",
        })
        self.fields["password1"].widget.attrs.update({
            "class": "input", "placeholder": "Password", "autocomplete": "new-password",
        })
        self.fields["password2"].label = "Repeat password"
        self.fields["password2"].widget.attrs.update({
            "class": "input", "placeholder": "Repeat password",
            "autocomplete": "new-password",
        })

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("An account with that email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.role = User.Role.CLIENT
        user.is_active = True
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = ""
        self.fields["username"].widget = forms.TextInput(attrs={
            "class": "input",
            "placeholder": "Username",
            "autocomplete": "username",
            "autofocus": True,
            "required": True,
        })
        self.fields["password"].label = ""
        self.fields["password"].widget = forms.PasswordInput(attrs={
            "class": "input",
            "placeholder": "Password",
            "autocomplete": "current-password",
            "required": True,
        })


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = (
            "label", "full_name", "phone", "line1", "line2",
            "city", "region", "postal_code", "country", "is_default",
        )
        widgets = {
            "label": forms.Select(attrs={"class": "input"}),
            "full_name": forms.TextInput(attrs={"class": "input", "placeholder": "Full name"}),
            "phone": forms.TextInput(attrs={"class": "input", "placeholder": "Phone"}),
            "line1": forms.TextInput(attrs={"class": "input", "placeholder": "Street and number"}),
            "line2": forms.TextInput(attrs={"class": "input", "placeholder": "Apartment, floor (optional)"}),
            "city": forms.TextInput(attrs={"class": "input", "placeholder": "City"}),
            "region": forms.TextInput(attrs={"class": "input", "placeholder": "State / region"}),
            "postal_code": forms.TextInput(attrs={"class": "input", "placeholder": "Postcode"}),
            "country": forms.TextInput(attrs={"class": "input", "placeholder": "Country"}),
            "is_default": forms.CheckboxInput(attrs={"class": "checkbox"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["line2"].required = False
        self.fields["region"].required = False
        self.fields["postal_code"].required = False
        self.fields["phone"].required = False
        self.fields["is_default"].label = "Use as my default address"
        for name, field in self.fields.items():
            if name != "is_default":
                field.label = ""
