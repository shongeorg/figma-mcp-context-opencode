from __future__ import annotations

from django import forms

from .models import Order


class CheckoutForm(forms.Form):
    PAYMENT_CHOICES = [
        (Order.PaymentMethod.CARD, "Credit card"),
        (Order.PaymentMethod.BANK, "Direct bank transfer"),
        (Order.PaymentMethod.COD, "Cash on delivery"),
    ]

    full_name = forms.CharField(max_length=120, widget=forms.TextInput(
        attrs={"class": "input", "placeholder": "Full name", "autocomplete": "name"},
    ))
    email = forms.EmailField(widget=forms.EmailInput(
        attrs={"class": "input", "placeholder": "Email", "autocomplete": "email"},
    ))
    phone = forms.CharField(max_length=32, required=False, widget=forms.TextInput(
        attrs={"class": "input", "placeholder": "Phone", "autocomplete": "tel"},
    ))
    address_line = forms.CharField(max_length=200, widget=forms.TextInput(
        attrs={"class": "input", "placeholder": "Street and number",
               "autocomplete": "street-address"},
    ))
    city = forms.CharField(max_length=120, widget=forms.TextInput(
        attrs={"class": "input", "placeholder": "City", "autocomplete": "address-level2"},
    ))
    region = forms.CharField(max_length=120, required=False, widget=forms.TextInput(
        attrs={"class": "input", "placeholder": "State / region",
               "autocomplete": "address-level1"},
    ))
    postal_code = forms.CharField(max_length=16, required=False, widget=forms.TextInput(
        attrs={"class": "input", "placeholder": "Postcode", "autocomplete": "postal-code"},
    ))
    country = forms.CharField(max_length=80, initial="Ukraine", widget=forms.TextInput(
        attrs={"class": "input", "placeholder": "Country", "autocomplete": "country-name"},
    ))
    note = forms.CharField(max_length=1000, required=False, widget=forms.Textarea(
        attrs={"class": "input", "rows": 3, "placeholder": "Anything we should know?"},
    ))
    payment_method = forms.ChoiceField(
        choices=PAYMENT_CHOICES,
        initial=Order.PaymentMethod.COD,
        widget=forms.RadioSelect,
    )

    def clean_email(self):
        return (self.cleaned_data["email"] or "").strip().lower()

    def clean_payment_method(self):
        value = self.cleaned_data.get("payment_method")
        if value not in dict(self.PAYMENT_CHOICES):
            raise forms.ValidationError("Choose a payment method.")
        return value
