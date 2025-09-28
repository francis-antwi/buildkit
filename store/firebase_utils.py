import requests
import json
import os
from django.conf import settings

def send_firebase_otp(phone_number):
    """
    Safe Firebase OTP with automatic fallback
    """
    print(f"📞 Attempting to send OTP to: +233{phone_number}")
    
    # Always use fallback for now until Firebase is properly configured
    print("🔧 Using fallback mode (Firebase not configured)")
    return {
        'success': False,
        'error': 'Firebase not configured - using fallback'
    }

def verify_firebase_otp(session_info, verification_code):
    """
    Safe Firebase OTP verification with fallback
    """
    print(f"🔐 Firebase verification called but using fallback")
    return {
        'success': False,
        'error': 'Firebase not configured'
    }

def format_phone_for_firebase(phone_number):
    """
    Format phone number for Firebase Authentication
    """
    # Remove any non-digit characters
    phone_number = ''.join(filter(str.isdigit, phone_number))
    
    # Handle Ghana numbers (convert from 9-digit to international format)
    if phone_number.startswith('0'):
        phone_number = '233' + phone_number[1:]
    elif not phone_number.startswith('233') and len(phone_number) == 9:
        phone_number = '233' + phone_number
    
    # Add + prefix for international format
    if not phone_number.startswith('+'):
        phone_number = '+' + phone_number
    
    return phone_number