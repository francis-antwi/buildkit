# management/commands/cleanup_duplicates.py
from django.core.management.base import BaseCommand
from store.models import Product
from django.db.models import Count

class Command(BaseCommand):
    help = 'Clean up duplicate products'
    
    def handle(self, *args, **options):
        # Find duplicate product names
        duplicates = Product.objects.values('name').annotate(
            count=Count('id')
        ).filter(count__gt=1)
        
        total_deleted = 0
        
        for dup in duplicates:
            products = Product.objects.filter(name=dup['name']).order_by('id')
            # Keep the first one, delete the rest
            keep_product = products.first()
            delete_products = products.exclude(id=keep_product.id)
            
            delete_count = delete_products.count()
            delete_products.delete()
            
            total_deleted += delete_count
            self.stdout.write(
                self.style.WARNING(f"Deleted {delete_count} duplicates of '{keep_product.name}'")
            )
        
        self.stdout.write(
            self.style.SUCCESS(f"✅ Cleanup complete! Deleted {total_deleted} duplicate products")
        )
        self.stdout.write(
            self.style.SUCCESS(f"📊 Final count: {Product.objects.count()} products")
        )