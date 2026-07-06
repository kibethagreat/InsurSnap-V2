from decimal import Decimal

from django import forms

LOSS_CATEGORY_CHOICES = [
    ("auto", "Auto"),
    ("property", "Property"),
    ("liability", "Liability"),
    ("health", "Health"),
    ("travel", "Travel"),
    ("other", "Other"),
]


class ClaimSubmissionForm(forms.Form):
    policy_id = forms.CharField(
        label="Policy ID",
        max_length=64,
        widget=forms.TextInput(attrs={"placeholder": "e.g. POL-10293"}),
    )
    claim_amount = forms.DecimalField(
        label="Claim Amount ($)",
        min_value=Decimal("0.01"),
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(attrs={"step": "0.01", "placeholder": "e.g. 950.00"}),
    )
    loss_category = forms.ChoiceField(
        label="Loss Category",
        choices=LOSS_CATEGORY_CHOICES,
    )

    def clean_policy_id(self):
        return self.cleaned_data["policy_id"].strip().upper()
