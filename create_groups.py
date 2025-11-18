import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'buildkit.settings')
django.setup()

from store.models import SpecificationGroup

def create_spec_groups():
    groups = [
        {'name': 'electrical', 'display_name': 'Electrical Specifications', 'display_order': 1, 'icon_class': 'fas fa-bolt'},
        {'name': 'physical', 'display_name': 'Physical Specifications', 'display_order': 2, 'icon_class': 'fas fa-ruler-combined'},
        {'name': 'performance', 'display_name': 'Performance Specifications', 'display_order': 3, 'icon_class': 'fas fa-tachometer-alt'},
        {'name': 'safety', 'display_name': 'Safety Specifications', 'display_order': 4, 'icon_class': 'fas fa-shield-alt'},
        {'name': 'operational', 'display_name': 'Operational Specifications', 'display_order': 5, 'icon_class': 'fas fa-cogs'},
        {'name': 'general', 'display_name': 'General Specifications', 'display_order': 6, 'icon_class': 'fas fa-info-circle'},
    ]

    created_count = 0
    for group_data in groups:
        group, created = SpecificationGroup.objects.get_or_create(
            name=group_data['name'],
            defaults=group_data
        )
        if created:
            created_count += 1
            print(f'✅ Created specification group: {group.display_name}')
        else:
            print(f'⚠️ Specification group already exists: {group.display_name}')

    print(f'🎉 Successfully created {created_count} specification groups')

if __name__ == '__main__':
    create_spec_groups()