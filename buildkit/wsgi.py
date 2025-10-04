"""
WSGI config for buildkit project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'buildkit.settings')

application = get_wsgi_application()

# Vercel serverless function handler
# Add this section at the bottom of the file
try:
    from vercel_python.wsgi import RequestHandler
    app = RequestHandler(application)
except ImportError:
    # Fallback for local development
    print("Vercel WSGI adapter not found - running in local mode")
    pass