
from django.contrib import admin
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
import secrets
import os
from django.urls import include
# ============================================
# ADMIN SECURITY CONFIGURATION
# ============================================

# Generate or get the admin secret from environment
ADMIN_SECRET = os.environ.get('DJANGO_ADMIN_SECRET')


if not ADMIN_SECRET:
    raise Exception(
        "🚨 DJANGO_ADMIN_SECRET environment variable not set! "
        "Set it in Vercel dashboard under Project Settings → Environment Variables."
    )


ADMIN_SECRET_PATH = f"manage-{ADMIN_SECRET}/"

# Log the secret admin URL on server start
print("\n" + "="*60)
print("🚀 DJANGO ADMIN SECURITY CONFIGURATION")
print("="*60)
print(f"✅ REAL ADMIN URL: http://127.0.0.1:8000/{ADMIN_SECRET_PATH}")
print(f"📁 Secret file: {os.path.join(settings.BASE_DIR, '.admin_secret')}")
print("❌ Blocked paths: /admin/, /administrator/, /wp-admin/, etc.")
print("="*60 + "\n")

def admin_access_denied(request, extra_path=''):
    """Custom 403 page for admin access attempts"""
    return HttpResponseForbidden(
        """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>403 Forbidden - Admin Access Restricted</title>
            <style>
                * {
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }
                
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                    color: #333;
                    min-height: 100vh;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    padding: 20px;
                }
                
                .container {
                    background: white;
                    border-radius: 15px;
                    padding: 40px;
                    max-width: 600px;
                    width: 100%;
                    box-shadow: 0 10px 40px rgba(0,0,0,0.1);
                    text-align: center;
                    border: 1px solid #e0e0e0;
                }
                
                .lock-icon {
                    font-size: 64px;
                    color: #ff4757;
                    margin-bottom: 20px;
                }
                
                h1 {
                    color: #2d3436;
                    margin-bottom: 15px;
                    font-size: 28px;
                    font-weight: 600;
                }
                
                .subtitle {
                    color: #636e72;
                    margin-bottom: 25px;
                    font-size: 16px;
                    line-height: 1.6;
                }
                
                .security-alert {
                    background: #fff5f5;
                    border: 1px solid #ffcccc;
                    border-radius: 8px;
                    padding: 15px;
                    margin: 25px 0;
                    text-align: left;
                }
                
                .alert-title {
                    color: #e53e3e;
                    font-weight: 600;
                    margin-bottom: 8px;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                }
                
                .error-info {
                    background: #f8f9fa;
                    padding: 15px;
                    border-radius: 8px;
                    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
                    margin: 20px 0;
                    color: #495057;
                    border: 1px solid #dee2e6;
                    font-size: 14px;
                }
                
                .error-code {
                    color: #dc3545;
                    font-weight: bold;
                }
                
                .actions {
                    margin-top: 30px;
                    display: flex;
                    gap: 15px;
                    justify-content: center;
                    flex-wrap: wrap;
                }
                
                .btn {
                    padding: 12px 24px;
                    border-radius: 6px;
                    text-decoration: none;
                    font-weight: 500;
                    transition: all 0.2s ease;
                    border: none;
                    cursor: pointer;
                    font-size: 14px;
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                    gap: 8px;
                }
                
                .btn-primary {
                    background: #007bff;
                    color: white;
                }
                
                .btn-primary:hover {
                    background: #0056b3;
                    transform: translateY(-1px);
                    box-shadow: 0 4px 12px rgba(0,123,255,0.3);
                }
                
                .btn-secondary {
                    background: #6c757d;
                    color: white;
                }
                
                .btn-secondary:hover {
                    background: #545b62;
                    transform: translateY(-1px);
                }
                
                .contact-info {
                    margin-top: 25px;
                    padding-top: 20px;
                    border-top: 1px solid #e9ecef;
                    font-size: 13px;
                    color: #6c757d;
                }
                
                .timestamp {
                    margin-top: 10px;
                    font-size: 12px;
                    color: #adb5bd;
                }
                
                @media (max-width: 480px) {
                    .container {
                        padding: 25px;
                    }
                    
                    .lock-icon {
                        font-size: 48px;
                    }
                    
                    h1 {
                        font-size: 24px;
                    }
                    
                    .actions {
                        flex-direction: column;
                    }
                    
                    .btn {
                        width: 100%;
                    }
                }
            </style>
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        </head>
        <body>
            <div class="container">
                <div class="lock-icon">
                    <i class="fas fa-shield-alt"></i>
                </div>
                
                <h1>Admin Access Restricted</h1>
                
                <div class="subtitle">
                    <p>Access to the administration panel is strictly limited to authorized personnel.</p>
                    <p>This incident has been logged for security purposes.</p>
                </div>
                
                <div class="security-alert">
                    <div class="alert-title">
                        <i class="fas fa-exclamation-triangle"></i>
                        Security Notice
                    </div>
                    <p>Unauthorized access attempts to administrative interfaces are monitored and may result in account suspension or legal action.</p>
                </div>
                
                <div class="error-info">
                    <div><span class="error-code">Error 403:</span> Forbidden</div>
                    <div>Access to this resource is denied</div>
                    <div>Request Path: <span style="color: #6610f2;">""" + request.path + """</span></div>
                </div>
                
                <div class="actions">
                    <a href="/" class="btn btn-primary">
                        <i class="fas fa-home"></i>
                        Return to Homepage
                    </a>
                    <a href="/contact/" class="btn btn-secondary">
                        <i class="fas fa-envelope"></i>
                        Contact Support
                    </a>
                </div>
                
                <div class="contact-info">
                    <p>If you believe you should have access to this resource, please contact the system administrator.</p>
                    <div class="timestamp">
                        <i class="fas fa-clock"></i>
                        """ + str(request.timestamp if hasattr(request, 'timestamp') else '') + """
                    </div>
                </div>
            </div>
            
            <script>
                // Log the access attempt (client-side)
                console.warn('Admin access denied to path: """ + request.path + """');
                
                // Add timestamp
                document.addEventListener('DOMContentLoaded', function() {
                    const now = new Date();
                    const timestamp = now.toLocaleString();
                    document.querySelector('.timestamp').innerHTML += 'Access attempt: ' + timestamp;
                });
            </script>
        </body>
        </html>
        """,
        content_type="text/html"
    )
def custom_admin_wrapper(request, extra_path=''):
    """Wrapper for admin site that adds logging and additional checks"""
    # Log admin access attempt
    user_ip = request.META.get('REMOTE_ADDR', '')
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    print(f"\n🔐 ADMIN ACCESS ATTEMPT:")
    print(f"   Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   IP: {user_ip}")
    print(f"   User: {request.user if request.user.is_authenticated else 'Anonymous'}")
    print(f"   Path: {request.path}")
    print(f"   Agent: {user_agent[:100]}...")
    
    # Check if user is authenticated and is staff
    if not request.user.is_authenticated:
        print("   ❌ Not authenticated - redirecting to login")
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    
    if not request.user.is_staff:
        print(f"   ❌ User '{request.user}' is not staff - denying access")
        return HttpResponseForbidden(
            "<h1>Access Denied</h1>"
            "<p>You do not have permission to access the admin panel.</p>"
            "<p>Your account does not have staff privileges.</p>"
        )
    
    print(f"   ✅ User '{request.user}' granted admin access")
    
    # FIXED: Proper way to handle admin URLs
    # admin.site.urls returns (urlpatterns, app_name, namespace)
    # We need to extract just the urlpatterns
    admin_urlpatterns = admin.site.urls[0]
    
    # Use Django's URL resolver
    from django.urls import URLResolver, get_resolver
    from django.urls.resolvers import RegexPattern
    
    # Create a resolver for admin URLs
    resolver = get_resolver(admin_urlpatterns)
    
    # Resolve the path (remove the secret prefix)
    path_to_resolve = request.path_info.replace(f'/manage-supersecret123/', '', 1)
    if not path_to_resolve:
        path_to_resolve = '/'
    
    try:
        # Try to resolve and call the view
        match = resolver.resolve(path_to_resolve)
        return match.func(request, *match.args, **match.kwargs)
    except Exception as e:
        # If resolution fails, show admin index
        print(f"   ⚠️  Could not resolve path: {e}")
        return admin.site.index(request)
# ============================================
# URL PATTERNS
# ============================================

import time  # For timestamp in logging

urlpatterns = [
    # REAL ADMIN (Secret URL)
    path(ADMIN_SECRET_PATH, custom_admin_wrapper),
    
    # MAIN APP ROUTES
    path('', include('store.urls')),
    path('cart/', include('cart.urls')),
    
    # BLOCKED ADMIN PATHS (Common admin URLs to block)
    path('admin/', admin_access_denied),
    path('admin/<path:extra_path>/', admin_access_denied),
    
    # Block common admin-like paths used by bots/hackers
    path('administrator/', admin_access_denied),
    path('administrator/<path:extra_path>/', admin_access_denied),
    
    path('wp-admin/', admin_access_denied),
    path('wp-admin/<path:extra_path>/', admin_access_denied),
    
    path('wp-login.php/', admin_access_denied),
    path('wp-login.php/<path:extra_path>/', admin_access_denied),
    
    path('dashboard/', admin_access_denied),
    path('dashboard/<path:extra_path>/', admin_access_denied),
    
    path('manager/', admin_access_denied),
    path('manager/<path:extra_path>/', admin_access_denied),
    
    path('control/', admin_access_denied),
    path('control/<path:extra_path>/', admin_access_denied),
    
    path('backend/', admin_access_denied),
    path('backend/<path:extra_path>/', admin_access_denied),
    
    path('admin.php/', admin_access_denied),
    path('admin.php/<path:extra_path>/', admin_access_denied),
    
    path('cp/', admin_access_denied),  # Control Panel
    path('cp/<path:extra_path>/', admin_access_denied),
    
    path('cpanel/', admin_access_denied),  # cPanel
    path('cpanel/<path:extra_path>/', admin_access_denied),
    
    path('administracion/', admin_access_denied),  # Spanish
    path('administracion/<path:extra_path>/', admin_access_denied),
    
    path('adminarea/', admin_access_denied),
    path('adminarea/<path:extra_path>/', admin_access_denied),
    
    path('panel/', admin_access_denied),
    path('panel/<path:extra_path>/', admin_access_denied),
    
    path('moderator/', admin_access_denied),
    path('moderator/<path:extra_path>/', admin_access_denied),
    
    # API/admin paths that should be blocked
    path('api/admin/', admin_access_denied),
    path('api/admin/<path:extra_path>/', admin_access_denied),
    
    path('api/v1/admin/', admin_access_denied),
    path('api/v1/admin/<path:extra_path>/', admin_access_denied),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
    # Also serve the secret admin URL info in debug mode
    def admin_info(request):
        """Debug page showing admin info (only in DEBUG mode)"""
        if not settings.DEBUG:
            return admin_access_denied(request)
        
        from django.contrib.auth.decorators import login_required, user_passes_test
        
        @login_required
        @user_passes_test(lambda u: u.is_staff)
        def secured_info(request):
            return HttpResponse(
                f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Admin Security Info</title>
                    <style>
                        body {{ font-family: monospace; padding: 20px; }}
                        .info {{ background: #f0f0f0; padding: 20px; border-radius: 5px; margin: 20px 0; }}
                        .secret {{ background: #ffeb3b; padding: 10px; font-weight: bold; }}
                        .warning {{ color: red; }}
                    </style>
                </head>
                <body>
                    <h1>Admin Security Configuration</h1>
                    <div class="info">
                        <h3>Current Configuration:</h3>
                        <p><strong>Real Admin URL:</strong> <span class="secret">/{ADMIN_SECRET_PATH}</span></p>
                        <p><strong>Secret File:</strong> {os.path.join(settings.BASE_DIR, '.admin_secret')}</p>
                        <p><strong>Blocked Paths:</strong> /admin/, /administrator/, /wp-admin/, etc.</p>
                    </div>
                    <div class="warning">
                        <h3>⚠️ Warning:</h3>
                        <p>This page is only visible in DEBUG mode to staff users.</p>
                        <p>Make sure to disable DEBUG in production!</p>
                    </div>
                    <a href="/{ADMIN_SECRET_PATH}">Go to Admin Panel →</a>
                </body>
                </html>
                """
            )
        
        return secured_info(request)
    
    urlpatterns.append(path('admin-info/', admin_info))