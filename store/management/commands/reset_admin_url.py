# store/management/commands/reset_admin_url.py
from django.core.management.base import BaseCommand
import secrets
import os
from django.conf import settings

class Command(BaseCommand):
    help = 'Reset the secret admin URL'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force reset even if file exists',
        )
    
    def handle(self, *args, **options):
        secret_file = os.path.join(settings.BASE_DIR, '.admin_secret')
        
        if os.path.exists(secret_file) and not options['force']:
            self.stdout.write(self.style.WARNING(f"⚠️  Secret file already exists: {secret_file}"))
            self.stdout.write(self.style.WARNING("Use --force to overwrite"))
            return
        
        # Generate new secret
        new_secret = secrets.token_urlsafe(32)
        
        with open(secret_file, 'w') as f:
            f.write(new_secret)
        
        new_admin_url = f"/manage-{new_secret}/"
        
        self.stdout.write(self.style.SUCCESS("="*60))
        self.stdout.write(self.style.SUCCESS("🔄 ADMIN URL RESET SUCCESSFUL"))
        self.stdout.write(self.style.SUCCESS("="*60))
        self.stdout.write(self.style.SUCCESS(f"✅ New secret saved to: {secret_file}"))
        self.stdout.write(self.style.SUCCESS(f"🔗 NEW Admin URL: http://127.0.0.1:8000{new_admin_url}"))
        self.stdout.write(self.style.WARNING("⚠️  IMPORTANT: Update any bookmarks or scripts!"))
        self.stdout.write(self.style.SUCCESS("="*60))