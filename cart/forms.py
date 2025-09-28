from django import forms
import re
from django import forms
from django.core.exceptions import ValidationError
from store.models import UserProfile


class CartAddProductForm(forms.Form):
    quantity = forms.IntegerField(min_value=1, initial=1, widget=forms.NumberInput(attrs={'class': 'input-text qty text'}))
    override = forms.BooleanField(required=False, initial=False, widget=forms.HiddenInput)
class DeliveryCalculatorForm(forms.Form):
    calc_delivery_country = forms.ChoiceField(
        choices=[('GH', 'Ghana')], 
        initial='GH', 
        widget=forms.HiddenInput
    )
    region = forms.ChoiceField(
        choices=[
            ('', 'Select a region…'),
            ('Ahafo', 'Ahafo'),
            ('Ashanti', 'Ashanti'),
            ('Bono', 'Bono'),
            ('Bono East', 'Bono East'),
            ('Central', 'Central'),
            ('Eastern', 'Eastern'),
            ('Greater Accra', 'Greater Accra'),
            ('North East', 'North East'),
            ('Northern', 'Northern'),
            ('Oti', 'Oti'),
            ('Savannah', 'Savannah'),
            ('Upper East', 'Upper East'),
            ('Upper West', 'Upper West'),
            ('Volta', 'Volta'),
            ('Western', 'Western'),
            ('Western North', 'Western North'),
        ], 
        required=True, 
        label="Region"
    )
    first_name = forms.CharField(max_length=50, required=False, label="First Name")
    last_name = forms.CharField(max_length=50, required=False, label="Last Name")
    email = forms.EmailField(required=False, label="Email Address")
    phone_number = forms.CharField(
        max_length=13, 
        required=False, 
        label="Phone Number", 
        help_text="Enter phone number in format +1234567890"
    )
    address = forms.CharField(max_length=250, required=True, label="Address")
    city = forms.CharField(max_length=100, required=True, label="City")
    postal_code = forms.CharField(max_length=20, required=False, label="Postal Code")
    delivery_method = forms.ChoiceField(
        choices=[('free', 'Free Shipping'), ('flat', 'Flat Rate')],
        widget=forms.RadioSelect,
        initial='free',
        required=True,
        label="Delivery Method"
    )

    def __init__(self, *args, **kwargs):
        self.user_is_authenticated = kwargs.pop('user_is_authenticated', False)
        super().__init__(*args, **kwargs)
        
        # For non-authenticated users, make personal info required
        if not self.user_is_authenticated:
            self.fields['first_name'].required = True
            self.fields['last_name'].required = True
            self.fields['email'].required = True
            self.fields['phone_number'].required = True

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        # Only validate if phone number is provided and user is not authenticated
        if phone_number and not self.user_is_authenticated:
            if not re.match(r'^\+[0-9]{10,12}$', phone_number):
                raise forms.ValidationError("Please enter a valid phone number (e.g., +1234567890)")
        return phone_number


class UserProfileForm(forms.ModelForm):
    phone_number = forms.CharField(
        required=False,
        max_length=13,
        widget=forms.TextInput(attrs={
            'placeholder': '+233598670304',
            'class': 'form-control',
        }),
        help_text="Enter phone number in international format (e.g., +233598670304)"
    )

    class Meta:
        model = UserProfile
        fields = ['phone_number']

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        
        # If empty, return None
        if not phone_number or phone_number.strip() == '':
            return None
        
        # Clean up whitespace
        phone_number = phone_number.strip()
        
        # Validate format
        if not re.match(r'^\+\d{1,3}\d{6,12}$', phone_number):
            raise ValidationError(
                "Phone number must be in international format starting with + "
                "followed by country code and number (e.g., +233598670304)"
            )
        
        # Check for uniqueness (excluding current instance)
        existing = UserProfile.objects.filter(phone_number=phone_number)
        if self.instance and self.instance.pk:
            existing = existing.exclude(pk=self.instance.pk)
        
        if existing.exists():
            raise ValidationError("This phone number is already registered.")
        
        return phone_number

    def save(self, commit=True):
        """Override save to handle phone number properly"""
        instance = super().save(commit=False)
        
        # Ensure empty phone numbers become None
        if not self.cleaned_data.get('phone_number'):
            instance.phone_number = None
        
        if commit:
            instance.save()
        return instance