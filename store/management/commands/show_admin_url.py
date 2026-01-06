# store/management/commands/show_admin_url.py
from django.core.management.base import BaseCommand
import os
from django.conf import settings

class Command(BaseCommand):
    help = 'Show the current secret admin URL'
    
    def handle(self, *args, **options):
        secret_file = os.path.join(settings.BASE_DIR, '.admin_secret')
        
        try:
            with open(secret_file, 'r') as f:
                admin_secret = f.read().strip()
                admin_url = f"/manage-{admin_secret}/"
                
                self.stdout.write(self.style.SUCCESS("="*60))
                self.stdout.write(self.style.SUCCESS("🔐 ADMIN PANEL INFORMATION"))
                self.stdout.write(self.style.SUCCESS("="*60))
                self.stdout.write(self.style.SUCCESS(f"📁 Secret file: {secret_file}"))
                self.stdout.write(self.style.SUCCESS(f"🔗 Admin URL: http://127.0.0.1:8000{admin_url}"))
                self.stdout.write(self.style.WARNING("❌ Blocked: /admin/, /administrator/, /wp-admin/, etc."))
                self.stdout.write(self.style.SUCCESS("="*60))
                
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"❌ Secret file not found: {secret_file}"))
            self.stdout.write(self.style.WARNING("Run the server once to generate the secret file."))