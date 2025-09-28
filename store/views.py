from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.models import Q, Avg
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
from .firebase_utils import send_firebase_otp, verify_firebase_otp, format_phone_for_firebase
import time
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

User = get_user_model()
logger = logging.getLogger(__name__)

def index(request):
    testimonials = Testimonial.objects.filter(approved=True).order_by('-created')[:4]
    context = {
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
    product = get_object_or_404(Product, slug=slug, available=True)
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
    building_materials = Product.objects.filter(product_type='material', available=True)[:6]
    construction_tools = Product.objects.filter(product_type='tool', available=True)[:6]
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

def register(request):
    print("🔄 ===== REGISTER VIEW START =====")
    
    # Clear session data when accessing the registration page via GET
    if request.method == 'GET':
        # Only clear if coming from outside the verification flow
        referer = request.META.get('HTTP_REFERER', '')
        if 'verification' not in referer and 'register' not in referer:
            cleanup_session(request)
            print("🧹 Session cleaned up on GET request")
    
    if request.method == 'POST' and 'verification_code' not in request.POST:
        print("📝 Processing INITIAL registration form")
        
        # DEBUG: Check user count before form validation
        user_count_before = User.objects.count()
        print(f"👥 Users before form validation: {user_count_before}")
        
        form = RegistrationForm(request.POST)
        
        if form.is_valid():
            print("✅ Form is valid - SHOULD NOT CREATE USER YET")
            
            # DEBUG: Check user count after form validation
            user_count_after = User.objects.count()
            print(f"👥 Users after form validation: {user_count_after}")
            
            username = form.cleaned_data['username']
            
            # Check if user was created during form processing
            if User.objects.filter(username=username).exists():
                print(f"🚨 CRITICAL ERROR: User {username} was created during form processing!")
                print("🔍 This means the form or something in form validation is creating users")
                messages.error(request, 'System error: User was created unexpectedly. Please contact support.')
                cleanup_session(request)
                return redirect('store:register')
            else:
                print(f"✅ Good: User {username} does not exist yet - proceeding to OTP")
            
            # Store cleaned form data in session (DON'T save user yet)
            request.session['registration_data'] = {
                'username': form.cleaned_data['username'],
                'full_name': form.cleaned_data['full_name'],
                'email': form.cleaned_data['email'],
                'phone_number': form.cleaned_data['phone_number'],
                'password': form.cleaned_data['password1'],
            }
            
            # FORCE FALLBACK MODE FOR NOW (until Firebase is configured)
            phone_number = form.cleaned_data['phone_number']
            verification_code = str(random.randint(100000, 999999))
            
            request.session['verification_code'] = verification_code
            request.session['verification_code_created_at'] = str(time.time())
            request.session['using_firebase'] = False
            
            print(f"📱 Using FALLBACK mode. Code for +233{phone_number}: {verification_code}")
            print(f"💾 Session after storing: {dict(request.session)}")
            
            messages.info(request, f"📱 Verification code: {verification_code}")
            return render(request, 'auth/register.html', {'verification_form': VerificationForm()})
        else:
            print("❌ Form validation failed")
            messages.error(request, 'Please correct the errors below.')
    
    elif request.method == 'POST' and 'verification_code' in request.POST:
        print("🔐 Processing verification form")
        
        # DEBUG: Check user count before verification
        user_count_before_verify = User.objects.count()
        print(f"👥 Users before verification: {user_count_before_verify}")
        
        verification_form = VerificationForm(request.POST)
        if verification_form.is_valid():
            entered_code = verification_form.cleaned_data['verification_code']
            
            print(f"🔑 Verifying code: {entered_code}")
            print(f"📋 Session data before verification: {dict(request.session)}")
            
            # Check if using Firebase or fallback
            if request.session.get('using_firebase') and 'firebase_session_info' in request.session:
                print("🔑 Using Firebase verification")
                session_info = request.session['firebase_session_info']
                verification_result = verify_firebase_otp(session_info, entered_code)
                
                if verification_result['success']:
                    print("✅ Firebase verification successful!")
                    return complete_registration(request)
                else:
                    print(f"❌ Firebase verification failed: {verification_result['error']}")
                    messages.error(request, f"Invalid verification code: {verification_result['error']}")
                    return render(request, 'auth/register.html', {'verification_form': VerificationForm()})
            
            else:
                # Fallback manual verification
                stored_code = request.session.get('verification_code')
                print(f"🔑 Using fallback verification. Stored: {stored_code}, Entered: {entered_code}")
                
                # Code expiry check (10 minutes)
                code_created_at = request.session.get('verification_code_created_at')
                if code_created_at and (time.time() - float(code_created_at) > 600):
                    print("⏰ Code expired")
                    messages.error(request, 'Verification code has expired. Please register again.')
                    cleanup_session(request)
                    return redirect('store:register')
                
                if entered_code == stored_code:
                    print("✅ Verification successful! Creating user...")
                    return complete_registration(request)
                else:
                    print(f"❌ Verification failed. Stored: {stored_code}, Entered: {entered_code}")
                    messages.error(request, 'Invalid verification code.')
                    return render(request, 'auth/register.html', {'verification_form': VerificationForm()})
        else:
            print("❌ Verification form invalid")
    
    else:
        print("📄 Loading empty registration form")
        form = RegistrationForm()
    
    return render(request, 'auth/register.html', {'form': form})

def complete_registration(request):
    """Complete user registration after successful verification"""
    print("👤 Starting complete_registration")
    
    registration_data = request.session.get('registration_data')
    
    if not registration_data:
        print("❌ No registration data in session")
        messages.error(request, 'Registration session expired. Please try again.')
        return redirect('store:register')
    
    print(f"📦 Registration data: {registration_data}")
    
    try:
        # DOUBLE CHECK: Verify user doesn't already exist
        username = registration_data['username']
        email = registration_data['email']
        
        if User.objects.filter(username=username).exists():
            print(f"❌ User {username} already exists!")
            messages.error(request, 'Username already exists. Please try again with a different username.')
            cleanup_session(request)
            return redirect('store:register')
        
        if User.objects.filter(email=email).exists():
            print(f"❌ Email {email} already exists!")
            messages.error(request, 'Email already exists. Please try again with a different email.')
            cleanup_session(request)
            return redirect('store:register')
        
        print(f"✅ Creating user: {username}")
        
        # ONLY CREATE USER HERE - after verification
        user = User.objects.create_user(
            username=username,
            email=email,
            password=registration_data['password']
        )
        
        # Set first and last name
        full_name = registration_data['full_name']
        first_name, *last_name = full_name.split(' ', 1)
        user.first_name = first_name
        user.last_name = last_name[0] if last_name else ''
        user.save()
        
        print(f"✅ User created: {user.username}")
        
        # Create user profile with phone number
        phone_number = f"+233{registration_data['phone_number']}"
        UserProfile.objects.create(user=user, phone_number=phone_number)
        print(f"✅ User profile created with phone: {phone_number}")
        
        # Log the user in - FIXED: Use authenticate to handle multiple backends
        authenticated_user = authenticate(
            request, 
            username=username, 
            password=registration_data['password']
        )
        
        if authenticated_user is not None:
            login(request, authenticated_user)
            print("✅ User logged in successfully")
        else:
            # Fallback: Set backend manually
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, user)
            print("✅ User logged in with manual backend")
        
        # Clean up session
        cleanup_session(request)
        
        print("✅ Registration completed successfully!")
        messages.success(request, 'Registration successful! You are now logged in.')
        return redirect('store:index')
        
    except Exception as e:
        print(f"❌ Registration failed: {e}")
        messages.error(request, f'Registration failed: {str(e)}')
        # Clean up session on error too
        cleanup_session(request)
        return redirect('store:register')

def cleanup_session(request):
    """Clean up session data"""
    print("🧹 Cleaning up session")
    keys_to_remove = [
        'registration_data', 
        'verification_code', 
        'verification_code_created_at',
        'firebase_session_info',
        'using_firebase'
    ]
    
    for key in keys_to_remove:
        if key in request.session:
            del request.session[key]
            print(f"   Removed: {key}")
    
    # Also clear any form data from previous attempts
    if 'form_data' in request.session:
        del request.session['form_data']

def clear_registration_session(request):
    """Clear registration session data"""
    cleanup_session(request)
    messages.info(request, "Registration session cleared. You can start over.")
    return redirect('store:register')

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

@require_POST
@csrf_exempt
def resend_verification(request):
    """Resend verification code"""
    try:
        registration_data = request.session.get('registration_data')
        if not registration_data:
            return JsonResponse({'success': False, 'error': 'Session expired'})
        
        phone_number = registration_data['phone_number']
        formatted_phone = format_phone_for_firebase(phone_number)
        
        # Resend Firebase OTP
        otp_result = send_firebase_otp(formatted_phone)
        
        if otp_result['success']:
            request.session['firebase_session_info'] = otp_result['session_info']
            request.session['verification_code_created_at'] = str(time.time())
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': otp_result['error']})
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})