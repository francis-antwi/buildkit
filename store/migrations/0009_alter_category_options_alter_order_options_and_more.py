from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('store', '0008_alter_userprofile_phone_number'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='category',
            options={'ordering': ['name'], 'verbose_name_plural': 'Categories'},
        ),
        migrations.AlterModelOptions(
            name='order',
            options={'ordering': ['-created']},
        ),
        migrations.AlterModelOptions(
            name='product',
            options={'ordering': ['-created']},
        ),
        migrations.AlterModelOptions(
            name='productimage',
            options={'ordering': ['-is_primary', 'id']},
        ),
        migrations.AlterModelOptions(
            name='testimonial',
            options={'ordering': ['-created']},
        ),
        migrations.AlterModelOptions(
            name='userprofile',
            options={'verbose_name': 'User Profile', 'verbose_name_plural': 'User Profiles'},
        ),
        migrations.AddField(
            model_name='category',
            name='created',
            field=models.DateTimeField(auto_now_add=True),  # Removed default=1
        ),
        migrations.AddField(
            model_name='category',
            name='updated',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='productimage',
            name='is_primary',
            field=models.BooleanField(default=False, help_text='Use as main product image'),
        ),
        migrations.AlterField(
            model_name='category',
            name='name',
            field=models.CharField(max_length=100, unique=True),
        ),
        migrations.AlterField(
            model_name='category',
            name='slug',
            field=models.SlugField(help_text='URL-friendly version of the name', unique=True),
        ),
        migrations.AlterField(
            model_name='product',
            name='category',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='products', to='store.category'),
        ),
        migrations.AlterField(
            model_name='product',
            name='slug',
            field=models.SlugField(help_text='URL-friendly version of the name', unique=True),
        ),
        migrations.AlterField(
            model_name='productimage',
            name='alt_text',
            field=models.CharField(blank=True, help_text='Alternative text for accessibility', max_length=100),
        ),
        migrations.AlterField(
            model_name='testimonial',
            name='rating',
            field=models.PositiveIntegerField(choices=[(1, '1 Star'), (2, '2 Stars'), (3, '3 Stars'), (4, '4 Stars'), (5, '5 Stars')], default=5),
        ),
        migrations.AlterUniqueTogether(
            name='orderitem',
            unique_together={('order', 'product')},
        ),
        migrations.AlterUniqueTogether(
            name='testimonial',
            unique_together={('product', 'user')},
        ),
        migrations.AddIndex(
            model_name='order',
            index=models.Index(fields=['user', 'created'], name='store_order_user_id_ea0ccc_idx'),
        ),
        migrations.AddIndex(
            model_name='order',
            index=models.Index(fields=['status', 'created'], name='store_order_status_67d3de_idx'),
        ),
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['category', 'available'], name='store_produ_categor_b49ff2_idx'),
        ),
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['product_type', 'available'], name='store_produ_product_8fb327_idx'),
        ),
    ]