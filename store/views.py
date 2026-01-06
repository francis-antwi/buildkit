from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.models import Q, Avg, Count
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction, IntegrityError
from .models import Category, Product, Testimonial, UserProfile
from cart.forms import CartAddProductForm
from .forms import RegistrationForm, VerificationForm
import random
import logging
import re
import json
from .firebase_utils import send_firebase_otp, verify_firebase_otp, format_phone_for_firebase
import time
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
from django.views.decorators.csrf import ensure_csrf_cookie

User = get_user_model()
logger = logging.getLogger(__name__)

def get_firebase_context():
    """Return Firebase configuration for templates"""
    return {
        'FIREBASE_WEB_API_KEY': settings.FIREBASE_WEB_API_KEY,
        'FIREBASE_AUTH_DOMAIN': settings.FIREBASE_AUTH_DOMAIN,
        'FIREBASE_PROJECT_ID': settings.FIREBASE_PROJECT_ID,
        'FIREBASE_APP_ID': settings.FIREBASE_APP_ID,
        'FIREBASE_MESSAGING_SENDER_ID': settings.FIREBASE_MESSAGING_SENDER_ID,
        'FIREBASE_STORAGE_BUCKET': settings.FIREBASE_STORAGE_BUCKET,
    }

def cleanup_session(request):
    """Clean up session data"""
    print("🧹 Cleaning up session")
    keys_to_remove = [
        'registration_data', 
        'verification_code', 
        'verification_code_created_at',
        'firebase_phone_number',
        'using_firebase',
        'firebase_verification_id',
        'firebase_verified',
        'firebase_uid',
        'firebase_phone_verified',
        'firebase_id_token'
    ]
    
    for key in keys_to_remove:
        if key in request.session:
            del request.session[key]
            print(f"   Removed: {key}")
    
    if 'form_data' in request.session:
        del request.session['form_data']

def index(request):
    # Get ALL service categories (remove featured filter)
    service_categories = Category.objects.filter(
        service_type__isnull=False
    ).exclude(service_type='').order_by('display_order', 'name')[:50]
    
    print("🔍 DEBUG - Service categories in index view:")
    for i, cat in enumerate(service_categories):
        print(f"   {i+1}. {cat.name} (slug: {cat.slug})")
    print(f"   Total categories found: {service_categories.count()}")
    
    featured_products = Product.objects.filter(featured=True, available=True)[:8]
    testimonials = Testimonial.objects.filter(approved=True).order_by('-created')[:4]
    
    context = {
        'featured_categories': service_categories,
        'featured_products': featured_products,
        'testimonials': testimonials,
    }
    return render(request, 'index.html', context)

def product_list(request, category_slug=None):
    category = None
    categories = Category.objects.all()
    products = Product.objects.filter(available=True).select_related('category').order_by('id')
    
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)
    
    query = request.GET.get('q')
    if query:
        products = products.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query)
        )
    
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    top_rated_products = Product.objects.filter(
        testimonials__approved=True
    ).annotate(
        avg_rating=Avg('testimonials__rating')
    ).order_by('-avg_rating')[:3]
    
    product_forms = {product.id: CartAddProductForm(initial={'quantity': 1, 'override': False}) for product in page_obj}
    
    context = {
        'category': category,
        'categories': categories,
        'products': page_obj,
        'query': query,
        'top_rated_products': top_rated_products,
        'product_forms': product_forms,
    }
    return render(request, 'store/index.html', context)

def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.select_related('category')
                      .prefetch_related('images', 'testimonials', 'technical_specs'),
        slug=slug, 
        available=True
    )
    
    cart_product_form = CartAddProductForm(initial={'quantity': 1, 'override': False})
    approved_testimonials = product.testimonials.filter(approved=True)
    avg_rating = approved_testimonials.aggregate(avg_rating=Avg('rating'))['avg_rating'] or 0
    review_count = approved_testimonials.count()
    
    related_products = Product.objects.filter(
        category=product.category, 
        available=True
    ).exclude(id=product.id)[:4]
    
    related_products_with_ratings = []
    for related_product in related_products:
        related_approved = related_product.testimonials.filter(approved=True)
        related_avg_rating = related_approved.aggregate(avg_rating=Avg('rating'))['avg_rating'] or 0
        related_review_count = related_approved.count()
        related_products_with_ratings.append({
            'product': related_product,
            'avg_rating': related_avg_rating,
            'review_count': related_review_count,
        })
    
    context = {
        'product': product,
        'cart_product_form': cart_product_form,
        'avg_rating': avg_rating,
        'review_count': review_count,
        'approved_testimonials': approved_testimonials,
        'related_products_with_ratings': related_products_with_ratings,
    }
    return render(request, 'store/detail.html', context)

@login_required
def add_review(request, product_id):
    product = get_object_or_404(Product, id=product_id, available=True)
    if request.method == 'POST':
        rating = request.POST.get('rating')
        content = request.POST.get('content')
        if rating and content:
            Testimonial.objects.create(
                product=product,
                user=request.user,
                reviewer_name=request.user.first_name or request.user.username,
                rating=rating,
                content=content,
                approved=False
            )
            messages.success(request, 'Your review has been submitted and is pending approval.')
            return redirect('store:product_detail', slug=product.slug)
        else:
            messages.error(request, 'Please provide a rating and review content.')
    return redirect('store:product_detail', slug=product.slug)

def store(request):
    featured_products = Product.objects.filter(available=True)[:8]
    building_materials = Product.objects.filter(product_type='material', available=True)[:50]
    construction_tools = Product.objects.filter(product_type='tool', available=True)[:50]
    categories = Category.objects.all()
    top_rated_products = Product.objects.filter(
        testimonials__approved=True
    ).annotate(
        avg_rating=Avg('testimonials__rating')
    ).order_by('-avg_rating')[:3]
    
    product_forms = {
        product.id: CartAddProductForm(initial={'quantity': 1, 'override': False})
        for product in list(featured_products) + list(building_materials) + list(construction_tools)
    }
    
    context = {
        'featured_products': featured_products,
        'building_materials': building_materials,
        'construction_tools': construction_tools,
        'categories': categories,
        'top_rated_products': top_rated_products,
        'products': list(featured_products) + list(building_materials) + list(construction_tools),
        'product_forms': product_forms,
    }
    return render(request, 'store/index.html', context)

@ensure_csrf_cookie
def register(request):
    print("🔄 ===== REGISTER VIEW START =====")
    
    # Get Firebase context
    firebase_context = get_firebase_context()
    
    # Clear session on GET request if coming from outside the registration flow
    if request.method == 'GET':
        referer = request.META.get('HTTP_REFERER', '')
        current_path = request.path
        
        # Only clean session if not coming from verification step
        if not ('/verify/' in referer or '/register/' in referer or 'verification' in referer):
            cleanup_session(request)
            print("🧹 Session cleaned up on GET request")
    
    # Handle initial registration form (Step 1)
    if request.method == 'POST' and 'verification_code' not in request.POST and 'firebase_id_token' not in request.POST:
        print("📝 Processing INITIAL registration form")
        
        form = RegistrationForm(request.POST)
        
        if form.is_valid():
            print("✅ Form is valid - storing data in session")
            
            # Check if user already exists
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            phone_number = form.cleaned_data['phone_number']
            
            if User.objects.filter(username=username).exists():
                messages.error(request, 'Username already exists.')
                return render(request, 'auth/register.html', {'form': form, **firebase_context})
            
            if User.objects.filter(email=email).exists():
                messages.error(request, 'Email already exists.')
                return render(request, 'auth/register.html', {'form': form, **firebase_context})
            
            # Format phone for Firebase
            formatted_phone = f"+233{phone_number}"
            
            # Store registration data in session
            request.session['registration_data'] = {
                'username': username,
                'full_name': form.cleaned_data['full_name'],
                'email': email,
                'phone_number': phone_number,
                'formatted_phone': formatted_phone,
                'password': form.cleaned_data['password1'],
            }
            
            # Try to send Firebase OTP
            try:
                print(f"📱 Attempting to send Firebase OTP to: {formatted_phone}")
                
                # This should return a verification ID that we need to store
                otp_result = send_firebase_otp(formatted_phone)
                
                if otp_result.get('success'):
                    # Store verification ID for later use
                    request.session['firebase_verification_id'] = otp_result.get('verification_id')
                    request.session['firebase_phone_number'] = formatted_phone
                    request.session['using_firebase'] = True
                    
                    print("✅ Firebase OTP sent successfully")
                    
                    # Redirect to verification page
                    return redirect('store:verify_phone')
                    
                else:
                    raise Exception(otp_result.get('error', 'Failed to send OTP'))
                    
            except Exception as e:
                print(f"❌ Firebase OTP failed: {e}")
                # Fallback to manual OTP
                verification_code = str(random.randint(100000, 999999))
                request.session['verification_code'] = verification_code
                request.session['verification_code_created_at'] = time.time()
                request.session['using_firebase'] = False
                
                print(f"📱 Using FALLBACK mode. Code for {formatted_phone}: {verification_code}")
                messages.info(request, f"📱 Verification code: {verification_code}")
                
                # Redirect to verification page
                return redirect('store:verify_phone')
        else:
            print("❌ Form validation failed")
            messages.error(request, 'Please correct the errors below.')
            
            context = {
                **firebase_context,
                'form': form,
            }
            return render(request, 'auth/register.html', context)
    
    # GET request - show registration form
    else:
        print("📄 Loading empty registration form")
        form = RegistrationForm()
        
        context = {
            **firebase_context,
            'form': form,
        }
        return render(request, 'auth/register.html', context)

def verify_phone_view(request):
    """Display phone verification page"""
    firebase_context = get_firebase_context()
    
    registration_data = request.session.get('registration_data')
    if not registration_data:
        messages.error(request, 'Registration session expired. Please start over.')
        return redirect('store:register')
    
    formatted_phone = registration_data.get('formatted_phone', '')
    phone_number = registration_data.get('phone_number', '')
    
    # Check if we have a verification code stored (manual fallback)
    verification_code = request.session.get('verification_code', '')
    using_firebase = request.session.get('using_firebase', False)
    
    # If using Firebase but no verification ID, try to resend
    if using_firebase and not request.session.get('firebase_verification_id'):
        try:
            otp_result = send_firebase_otp(formatted_phone)
            if otp_result.get('success'):
                request.session['firebase_verification_id'] = otp_result.get('verification_id')
                request.session['verification_code_created_at'] = time.time()
            else:
                # Fallback to manual
                verification_code = str(random.randint(100000, 999999))
                request.session['verification_code'] = verification_code
                request.session['verification_code_created_at'] = time.time()
                request.session['using_firebase'] = False
                using_firebase = False
                print(f"📱 Fallback to manual code: {verification_code}")
        except Exception as e:
            print(f"❌ Failed to resend Firebase OTP: {e}")
    
    context = {
        **firebase_context,
        'formatted_phone': formatted_phone,
        'phone_number': phone_number,
        'verification_code': verification_code,
        'using_firebase': using_firebase,
        'verification_form': VerificationForm(),
    }
    
    return render(request, 'auth/verify_phone.html', context)

# Handle manual verification form submission
@ensure_csrf_cookie
def verify_manual_otp(request):
    """Handle manual OTP verification"""
    print("🔐 Processing manual verification submission")
    
    if request.method != 'POST':
        return redirect('store:verify_phone')
    
    verification_form = VerificationForm(request.POST)
    
    if verification_form.is_valid():
        entered_code = verification_form.cleaned_data['verification_code']
        stored_code = request.session.get('verification_code')
        
        print(f"🔑 Entered: {entered_code}, Stored: {stored_code}")
        
        # Check code expiry (10 minutes)
        code_created_at = request.session.get('verification_code_created_at')
        if code_created_at and (time.time() - float(code_created_at) > 600):
            messages.error(request, 'Verification code has expired. Please register again.')
            cleanup_session(request)
            return redirect('store:register')
        
        if entered_code == stored_code:
            print("✅ Manual verification successful!")
            request.session['firebase_verified'] = True  # Mark as verified
            return complete_registration(request)
        else:
            messages.error(request, 'Invalid verification code.')
    else:
        messages.error(request, 'Please enter a valid verification code.')
    
    return redirect('store:verify_phone')

@csrf_exempt
@require_POST
def verify_firebase_token(request):
    """Verify Firebase ID token and complete registration"""
    try:
        data = json.loads(request.body)
        firebase_id_token = data.get('firebase_id_token')
        phone_number = data.get('phone_number')
        
        if not firebase_id_token:
            return JsonResponse({'success': False, 'error': 'Missing Firebase token'})
        
        # Verify the Firebase ID token
        from firebase_admin import auth
        from firebase_admin.exceptions import FirebaseError
        
        try:
            decoded_token = auth.verify_id_token(firebase_id_token)
            uid = decoded_token.get('uid')
            phone_number_from_token = decoded_token.get('phone_number')
            
            print(f"✅ Firebase token verified. UID: {uid}, Phone: {phone_number_from_token}")
            
            # Store verification success in session
            request.session['firebase_verified'] = True
            request.session['firebase_uid'] = uid
            request.session['firebase_phone_verified'] = phone_number_from_token
            
            # If phone number is provided, verify it matches
            if phone_number and phone_number_from_token != phone_number:
                return JsonResponse({'success': False, 'error': 'Phone number mismatch'})
            
            # Complete registration
            response = complete_registration(request)
            
            # If registration was successful, return success
            if response.status_code == 302 and response.url == '/':
                return JsonResponse({'success': True, 'redirect': '/'})
            else:
                return JsonResponse({'success': False, 'error': 'Registration failed after verification'})
            
        except FirebaseError as e:
            print(f"❌ Firebase token verification failed: {e}")
            return JsonResponse({'success': False, 'error': str(e)})
            
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'})
    except Exception as e:
        print(f"❌ Firebase verification error: {e}")
        return JsonResponse({'success': False, 'error': str(e)})

def complete_registration(request):
    """Complete user registration after successful verification"""
    print("👤 Starting complete_registration")
    
    registration_data = request.session.get('registration_data')
    
    if not registration_data:
        print("❌ No registration data in session")
        messages.error(request, 'Registration session expired. Please try again.')
        cleanup_session(request)
        return redirect('store:register')
    
    # Check if verified
    if not request.session.get('firebase_verified'):
        print("❌ User not verified")
        messages.error(request, 'Please verify your phone number first.')
        return redirect('store:verify_phone')
    
    print(f"📦 Registration data: {registration_data}")
    
    try:
        with transaction.atomic():
            # Create user
            user = User.objects.create_user(
                username=registration_data['username'],
                email=registration_data['email'],
                password=registration_data['password']
            )
            
            # Set name
            full_name = registration_data['full_name']
            name_parts = full_name.split(' ', 1)
            user.first_name = name_parts[0]
            user.last_name = name_parts[1] if len(name_parts) > 1 else ''
            user.save()
            
            print(f"✅ User created: {user.username}")
            
            # Create user profile
            phone_number = registration_data['formatted_phone']
            user_profile = UserProfile.objects.create(user=user, phone_number=phone_number)
            print(f"✅ User profile created with phone: {phone_number}")
            
            # Store Firebase UID if available
            firebase_uid = request.session.get('firebase_uid')
            if firebase_uid:
                user_profile.firebase_uid = firebase_uid
                user_profile.save()
                print(f"✅ Firebase UID stored: {firebase_uid}")
            
            # Log the user in
            authenticated_user = authenticate(
                request,
                username=registration_data['username'],
                password=registration_data['password']
            )
            
            if authenticated_user:
                login(request, authenticated_user)
                print("✅ User logged in successfully")
            else:
                # Fallback login
                user.backend = 'django.contrib.auth.backends.ModelBackend'
                login(request, user)
                print("✅ User logged in with manual backend")
            
            # Clean up session
            cleanup_session(request)
            
            print("✅ Registration completed successfully!")
            messages.success(request, 'Registration successful! You are now logged in.')
            return redirect('store:index')
            
    except IntegrityError as e:
        print(f"❌ Database error during registration: {e}")
        messages.error(request, 'User with this username or email already exists.')
        cleanup_session(request)
        return redirect('store:register')
    except Exception as e:
        print(f"❌ Registration failed: {e}")
        messages.error(request, f'Registration failed: {str(e)}')
        cleanup_session(request)
        return redirect('store:register')

@require_POST
@csrf_exempt
def resend_verification(request):
    """Resend verification code"""
    try:
        registration_data = request.session.get('registration_data')
        if not registration_data:
            return JsonResponse({'success': False, 'error': 'Session expired. Please start over.'})
        
        formatted_phone = registration_data['formatted_phone']
        
        # Check if using Firebase or fallback
        using_firebase = request.session.get('using_firebase', False)
        
        if using_firebase:
            # Resend Firebase OTP
            print(f"📱 Resending Firebase OTP to: {formatted_phone}")
            otp_result = send_firebase_otp(formatted_phone)
            
            if otp_result.get('success'):
                request.session['firebase_verification_id'] = otp_result.get('verification_id')
                request.session['verification_code_created_at'] = time.time()
                return JsonResponse({'success': True})
            else:
                # Fallback to manual
                verification_code = str(random.randint(100000, 999999))
                request.session['verification_code'] = verification_code
                request.session['verification_code_created_at'] = time.time()
                request.session['using_firebase'] = False
                
                print(f"📱 Fallback to manual code: {verification_code}")
                return JsonResponse({
                    'success': True,
                    'message': 'Code resent (fallback mode)',
                    'fallback': True,
                    'code': verification_code  # Remove in production
                })
        else:
            # Resend manual OTP
            print(f"📱 Resending manual OTP to: {formatted_phone}")
            verification_code = str(random.randint(100000, 999999))
            request.session['verification_code'] = verification_code
            request.session['verification_code_created_at'] = time.time()
            
            print(f"📱 New verification code: {verification_code}")
            
            return JsonResponse({
                'success': True,
                'message': 'Verification code resent',
                'code': verification_code  # Remove this in production
            })
            
    except Exception as e:
        print(f"❌ Error resending verification: {e}")
        return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
@require_POST
def verify_otp(request):
    """Verify OTP from Firebase"""
    try:
        data = json.loads(request.body)
        verification_id = request.session.get('firebase_verification_id')
        otp = data.get('otp')
        
        if not verification_id or not otp:
            return JsonResponse({'success': False, 'error': 'Missing verification data'})
        
        # Verify OTP using Firebase
        result = verify_firebase_otp(verification_id, otp)
        
        if result.get('success'):
            # Store verification success
            request.session['firebase_verified'] = True
            request.session['firebase_id_token'] = result.get('id_token')
            request.session['firebase_uid'] = result.get('uid')
            
            return JsonResponse({'success': True})
        else:
            return JsonResponse({
                'success': False,
                'error': result.get('error', 'Invalid OTP')
            })
            
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
@require_POST
def send_otp(request):
    """Send OTP to phone number"""
    try:
        data = json.loads(request.body)
        phone_number = data.get('phone_number')
        
        if not phone_number:
            return JsonResponse({'success': False, 'error': 'Phone number required'})
        
        # Format phone number
        formatted_phone = format_phone_for_firebase(phone_number)
        
        # Send OTP via Firebase
        result = send_firebase_otp(formatted_phone)
        
        if result.get('success'):
            # Store verification ID in session
            request.session['firebase_verification_id'] = result.get('verification_id')
            request.session['firebase_phone_number'] = formatted_phone
            request.session['using_firebase'] = True
            
            return JsonResponse({
                'success': True,
                'message': 'OTP sent successfully',
                'verification_id': result.get('verification_id')
            })
        else:
            # Fallback to manual OTP
            verification_code = str(random.randint(100000, 999999))
            request.session['verification_code'] = verification_code
            request.session['verification_code_created_at'] = time.time()
            request.session['using_firebase'] = False
            
            return JsonResponse({
                'success': True,
                'message': 'OTP sent (fallback mode)',
                'fallback': True,
                'code': verification_code  # Remove in production
            })
            
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

def login_view(request):
    return LoginView.as_view(template_name='auth/login.html', redirect_authenticated_user=True)(request)

def logout_view(request):
    return LogoutView.as_view(next_page='store:index')(request)

def product_list_by_category(request, category_slug):
    category = get_object_or_404(Category, slug=category_slug)
    products = Product.objects.filter(category=category, available=True).order_by('id')
    categories = Category.objects.all()
    top_rated_products = Product.objects.filter(
        testimonials__approved=True
    ).annotate(
        avg_rating=Avg('testimonials__rating')
    ).order_by('-avg_rating')[:3]
    
    product_forms = {product.id: CartAddProductForm(initial={'quantity': 1, 'override': False}) for product in products}
    
    context = {
        'category': category,
        'products': products,
        'categories': categories,
        'top_rated_products': top_rated_products,
        'product_forms': product_forms,
    }
    return render(request, 'store/index.html', context)

def service_category(request, category_slug):
    """
    Single view to handle all service categories using enhanced Category model
    """
    # Get the category by slug
    category = get_object_or_404(Category, slug=category_slug)
    
    # Get products for this category with related data
    products = Product.objects.filter(
        category=category, 
        available=True
    ).select_related('category').prefetch_related('testimonials')
    
    # Use category's own icon and color properties, fallback to defaults
    icon = category.icon_class if category.icon_class else 'fa-box'
    color = category.color_class if category.color_class else 'primary'
    btn_color = category.color_class if category.color_class else 'primary'
    
    # Get related categories (other service categories) - FIXED
    related_categories = Category.objects.filter(
        service_type__isnull=False
    ).exclude(service_type='').exclude(slug=category_slug)[:5]
    
    # Get featured products from this category
    featured_products = products.filter(featured=True)[:3]
    
    # Get product types distribution for this category - FIXED: Use Count instead of models.Count
    product_types = products.values('product_type').annotate(
        count=Count('id')
    ).order_by('-count')
    
    context = {
        'category': category,
        'products': products,
        'icon': icon,
        'color': color,
        'btn_color': btn_color,
        'related_categories': related_categories,
        'featured_products': featured_products,
        'product_types': product_types,
        'product_count': products.count(),
    }
    
    return render(request, 'services/service_category.html', context)

def clear_registration_session(request):
    """Clear registration session data"""
    cleanup_session(request)
    messages.info(request, "Registration session cleared. You can start over.")
    return redirect('store:register')