from django import forms
from django.contrib.auth import get_user_model
from .models import UserProfile
import re

User = get_user_model()

class RegistrationForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Choose a username'
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address'
        })
    )
    full_name = forms.CharField(
        max_length=100, 
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your full name'
        })
    )
    phone_number = forms.CharField(
        max_length=10, 
        required=True, 
        help_text="Enter your Ghana phone number without country code (e.g., 501234567)",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Phone number (e.g., 501234567)'
        })
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Create a password'
        }),
        required=True
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Confirm your password'
        }),
        required=True
    )

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("This username is already taken. Please choose a different one.")
        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email address is already registered. Please use a different email.")
        return email

    def clean_phone_number(self):
        phone_number = self.cleaned_data['phone_number']
        
        # Remove any non-digit characters
        phone_number = re.sub(r'\D', '', phone_number)
        
        # Validate Ghana phone number (9 digits, starts with 5, 2, 4, 6, etc.)
        if not re.match(r'^[2-9][0-9]{8}$', phone_number):
            raise forms.ValidationError(
                "Please enter a valid Ghana phone number (9 digits, e.g., 501234567)."
            )
        
        # Check if phone number already exists
        if UserProfile.objects.filter(phone_number=f"+233{phone_number}").exists():
            raise forms.ValidationError(
                "This phone number is already registered. Please use a different number."
            )
            
        return phone_number

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            self.add_error('password2', "Passwords don't match")
        
        return cleaned_data

class VerificationForm(forms.Form):
    verification_code = forms.CharField(
        max_length=6, 
        required=True, 
        help_text="Enter the 6-digit code sent to your phone",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter 6-digit code',
            'pattern': '[0-9]{6}',
            'maxlength': '6',
            'style': 'font-size: 1.2rem; letter-spacing: 0.5em; text-align: center;'
        })
    )
    
    def clean_verification_code(self):
        code = self.cleaned_data['verification_code']
        if not code.isdigit() or len(code) != 6:
            raise forms.ValidationError("Please enter a valid 6-digit code.")
        return code