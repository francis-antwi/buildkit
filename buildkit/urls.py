from django.contrib import admin
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
import secrets
import os
import time

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
    """Simple permission check then redirect to real admin"""
    # Check permissions
    if not request.user.is_authenticated:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    
    if not request.user.is_staff:
        return HttpResponseForbidden(
            "<h1>Access Denied</h1>"
            "<p>Staff privileges required to access admin panel.</p>"
        )
    
    # Log successful access
    print(f"✅ Admin access granted to: {request.user}")
    
    # Redirect to the REAL Django admin (which is included in urlpatterns below)
    from django.shortcuts import redirect
    
    # Extract path after secret prefix
    full_path = request.path_info
    secret_prefix = f"/manage-{ADMIN_SECRET}/"
    
    if full_path.startswith(secret_prefix):
        admin_subpath = full_path[len(secret_prefix):]
        # Remove leading slash if present
        if admin_subpath.startswith('/'):
            admin_subpath = admin_subpath[1:]
    else:
        admin_subpath = ''
    
    # Build redirect URL to the REAL admin (not blocked one)
    if admin_subpath:
        redirect_url = f'/real-admin/{admin_subpath}'
    else:
        redirect_url = '/real-admin/'
    
    print(f"🔐 Redirecting to: {redirect_url}")
    return redirect(redirect_url)

# ============================================
# URL PATTERNS
# ============================================

urlpatterns = [
    # REAL ADMIN (Secret URL) - this redirects after permission check
    path(ADMIN_SECRET_PATH, custom_admin_wrapper),
    path(ADMIN_SECRET_PATH + '<path:extra_path>/', custom_admin_wrapper),
    
    # ACTUAL Django admin (hidden at /real-admin/)
    # This is where the admin actually lives
    path('real-admin/', admin.site.urls),
    
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
    
    path('cp/', admin_access_denied),
    path('cp/<path:extra_path>/', admin_access_denied),
    
    path('cpanel/', admin_access_denied),
    path('cpanel/<path:extra_path>/', admin_access_denied),
    
    path('administracion/', admin_access_denied),
    path('administracion/<path:extra_path>/', admin_access_denied),
    
    path('adminarea/', admin_access_denied),
    path('adminarea/<path:extra_path>/', admin_access_denied),
    
    path('panel/', admin_access_denied),
    path('panel/<path:extra_path>/', admin_access_denied),
    
    path('moderator/', admin_access_denied),
    path('moderator/<path:extra_path>/', admin_access_denied),
    
    path('api/admin/', admin_access_denied),
    path('api/admin/<path:extra_path>/', admin_access_denied),
    
    path('api/v1/admin/', admin_access_denied),
    path('api/v1/admin/<path:extra_path>/', admin_access_denied),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Log the real admin URL
print(f"🔑 Real admin is at: /real-admin/")
print(f"🔐 Secret gateway: /{ADMIN_SECRET_PATH}")