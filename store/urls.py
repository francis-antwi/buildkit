from django.urls import path
from django.contrib.auth.views import LoginView
from . import views
from django.contrib.auth import views as auth_views
from .forms import CustomPasswordResetForm

app_name = 'store'

urlpatterns = [
    path('', views.index, name='index'),
    path('products/', views.product_list, name='product_list'),
    path('products/category/<slug:category_slug>/', views.product_list, name='product_list_by_category'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    path('login/', LoginView.as_view(template_name='auth/login.html', redirect_authenticated_user=True), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),
    path('products/<int:product_id>/review/', views.add_review, name='add_review'),
    path('admin-redirect/', views.redirect_to_admin, name='admin_redirect'),
    
    # Firebase OTP endpoints
    path('resend-verification/', views.resend_verification, name='resend_verification'),
    path('send-otp/', views.send_otp, name='send_otp'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('verify-firebase-token/', views.verify_firebase_token, name='verify_firebase_token'),
    path('verify-phone/', views.verify_phone_view, name='verify_phone'),
    
    # Registration session management
    path('register/clear/', views.clear_registration_session, name='clear_registration_session'),
    
    # Single service category view - REPLACES ALL INDIVIDUAL SERVICE VIEWS
    path('services/<slug:category_slug>/', views.service_category, name='service_category'),
    
    # Password reset URLs
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='auth/password_reset.html',
             email_template_name='auth/password_reset_email.html',
             subject_template_name='auth/password_reset_subject.txt',
             success_url='/password-reset/done/',
             form_class=CustomPasswordResetForm
         ), 
         name='password_reset'),
    
    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='auth/password_reset_done.html'
         ), 
         name='password_reset_done'),
    path('verify-manual-otp/', views.verify_manual_otp, name='verify_manual_otp'),
    
    path('password-reset-confirm/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name='auth/password_reset_confirm.html',
             success_url='/password-reset-complete/'
         ), 
         name='password_reset_confirm'),
    
    path('password-reset-complete/', 
         auth_views.PasswordResetCompleteView.as_view(
             template_name='auth/password_reset_complete.html'
         ), 
         name='password_reset_complete'),
]