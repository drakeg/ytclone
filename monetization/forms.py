from decimal import Decimal

from django import forms


class MembershipTierForm(forms.Form):
    name = forms.CharField(max_length=120)
    description = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}))
    monthly_price = forms.DecimalField(
        min_value=Decimal("0.50"),
        max_digits=8,
        decimal_places=2,
        help_text="Monthly price in USD.",
    )

    def price_minor(self):
        return int(self.cleaned_data["monthly_price"] * 100)
