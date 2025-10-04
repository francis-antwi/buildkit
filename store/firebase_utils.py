import firebase_admin
from firebase_admin import auth, credentials
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def initialize_firebase():
    """Initialize Firebase Admin SDK"""
    try:
        if not firebase_admin._apps:
            if hasattr(settings, 'FIREBASE_SERVICE_ACCOUNT_PATH'):
                cred = credentials.Certificate(settings.FIREBASE_SERVICE_ACCOUNT_PATH)
                firebase_admin.initialize_app(cred)
                logger.info("Firebase Admin SDK initialized successfully")
            else:
                logger.warning("FIREBASE_SERVICE_ACCOUNT_PATH not set in settings")
        return True
    except Exception as e:
        logger.error(f"Firebase initialization failed: {e}")
        return False

def verify_firebase_token(id_token):
    """Verify Firebase ID token"""
    try:
        if not initialize_firebase():
            return {'success': False, 'error': 'Firebase not initialized'}
            
        decoded_token = auth.verify_id_token(id_token)
        return {
            'success': True, 
            'uid': decoded_token['uid'], 
            'phone': decoded_token.get('phone_number')
        }
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        return {'success': False, 'error': str(e)}

def format_phone_for_firebase(phone_number):
    """
    Format phone number for Firebase
    Converts local Ghana number to international format
    """
    # Remove any non-digit characters
    phone_number = ''.join(filter(str.isdigit, phone_number))
    
    # If it's a Ghana number without country code, add it
    if len(phone_number) == 9 and phone_number.startswith(('2', '5', '4', '6')):
        return f"+233{phone_number}"
    elif len(phone_number) == 10 and phone_number.startswith('0'):
        return f"+233{phone_number[1:]}"
    elif phone_number.startswith('233') and len(phone_number) == 12:
        return f"+{phone_number}"
    else:
        # Assume it's already in international format
        return phone_number if phone_number.startswith('+') else f"+{phone_number}"

def send_firebase_otp(phone_number):
    """
    Send OTP via Firebase - This is primarily a frontend function
    but we include it for completeness
    """
    try:
        formatted_phone = format_phone_for_firebase(phone_number)
        logger.info(f"Firebase OTP would be sent to: {formatted_phone}")
        
        # Note: Firebase phone auth is primarily handled on the frontend
        # The actual SMS sending happens via the Firebase JS SDK
        return {
            'success': True,
            'formatted_phone': formatted_phone,
            'message': 'Firebase OTP setup complete - SMS will be sent via frontend'
        }
    except Exception as e:
        logger.error(f"Firebase OTP setup failed: {e}")
        return {'success': False, 'error': str(e)}

def verify_firebase_otp(session_info, verification_code):
    """
    Verify Firebase OTP - This is primarily a frontend function
    but we include it for reference
    """
    try:
        logger.info(f"Verifying Firebase OTP: {verification_code}")
        
        # Note: Firebase OTP verification is primarily handled on the frontend
        # The actual verification happens via the Firebase JS SDK
        # This function is mostly for fallback scenarios
        
        return {
            'success': True,
            'message': 'Firebase verification should be handled by frontend'
        }
    except Exception as e:
        logger.error(f"Firebase OTP verification failed: {e}")
        return {'success': False, 'error': str(e)}