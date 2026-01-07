# store/management/commands/show_admin_url.py
import os
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = 'Show the current secret admin URL'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--create',
            action='store_true',
            help='Create .admin_secret file from environment variable',
        )
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("="*60))
        self.stdout.write(self.style.SUCCESS("🔐 ADMIN PANEL INFORMATION"))
        self.stdout.write(self.style.SUCCESS("="*60))
        
        # Check environment variable
        env_secret = os.environ.get('DJANGO_ADMIN_SECRET')
        if env_secret:
            self.stdout.write(self.style.SUCCESS(f"✅ Found in environment: DJANGO_ADMIN_SECRET"))
            self.stdout.write(self.style.WARNING(f"🔑 Secret: {env_secret}"))
        else:
            self.stdout.write(self.style.WARNING("⚠️  No DJANGO_ADMIN_SECRET environment variable"))
        
        # Check file
        secret_file = os.path.join(settings.BASE_DIR, '.admin_secret')
        file_exists = os.path.exists(secret_file)
        
        if file_exists:
            with open(secret_file, 'r') as f:
                file_secret = f.read().strip()
                self.stdout.write(self.style.SUCCESS(f"✅ Found in file: {secret_file}"))
                self.stdout.write(self.style.WARNING(f"🔑 Secret: {file_secret}"))
        else:
            self.stdout.write(self.style.WARNING(f"❌ File not found: {secret_file}"))
        
        # Determine which secret to use
        active_secret = env_secret
        source = "environment variable"
        
        if not active_secret and file_exists:
            active_secret = file_secret
            source = "file"
        elif env_secret and file_exists:
            if env_secret == file_secret:
                source = "environment variable & file (match)"
            else:
                source = f"environment variable (file has different secret: {file_secret})"
        
        if active_secret:
            admin_url = f"/manage-{active_secret}/"
            self.stdout.write(self.style.SUCCESS("="*60))
            self.stdout.write(self.style.SUCCESS(f"🎯 ACTIVE ADMIN URL"))
            self.stdout.write(self.style.SUCCESS("="*60))
            self.stdout.write(self.style.SUCCESS(f"🔗 http://127.0.0.1:8000{admin_url}"))
            self.stdout.write(self.style.WARNING(f"📁 Source: {source}"))
            
            # Create file if requested
            if options['create'] and env_secret and not file_exists:
                with open(secret_file, 'w') as f:
                    f.write(env_secret)
                self.stdout.write(self.style.SUCCESS(f"📝 Created file: {secret_file}"))
        else:
            self.stdout.write(self.style.ERROR("="*60))
            self.stdout.write(self.style.ERROR("❌ NO ADMIN SECRET FOUND"))
            self.stdout.write(self.style.ERROR("="*60))
            self.stdout.write(self.style.WARNING("To fix this:"))
            self.stdout.write(self.style.WARNING("1. Set environment variable: set DJANGO_ADMIN_SECRET=your-secret"))
            self.stdout.write(self.style.WARNING("2. Or run: python manage.py show_admin_url --create"))
        
        self.stdout.write(self.style.SUCCESS("="*60))