from django.db import models
from django.urls import reverse
from cloudinary.models import CloudinaryField
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from decimal import Decimal
import re


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(
        max_length=13,
        unique=True,
        null=True,
        blank=True,
        help_text="Enter phone number in format +1234567890"
    )

    def clean(self):
        """Validate phone number format"""
        if self.phone_number and self.phone_number.strip():
            self.phone_number = self.phone_number.strip()
            if not re.match(r'^\+\d{1,3}\d{6,12}$', self.phone_number):
                raise ValidationError({
                    'phone_number': 'Phone number must be in international format (e.g., +233598670304)'
                })
        else:
            self.phone_number = None

    def save(self, *args, **kwargs):
        if not self.phone_number or self.phone_number.strip() == '':
            self.phone_number = None
        else:
            self.phone_number = self.phone_number.strip()
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Profile for {self.user.username}"

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"


class Category(models.Model):
    SERVICE_CATEGORIES = [
        ('building-materials', 'Building Materials'),
        ('construction-tools', 'Construction Tools'),
        ('finishing-materials', 'Finishing Materials'),
        ('plumbing-supplies', 'Plumbing Supplies'),
        ('electrical-supplies', 'Electrical Supplies'),
        ('roofing-materials', 'Roofing Materials'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(
        unique=True, 
        help_text="URL-friendly version of the name (e.g., 'building-materials')"
    )
    service_type = models.CharField(
        max_length=50, 
        choices=SERVICE_CATEGORIES,
        blank=True,
        help_text="Select if this is one of the main service categories"
    )
    description = models.TextField(blank=True)
    image = CloudinaryField('category_image', folder='buildkit/categories/', blank=True, null=True)
    icon_class = models.CharField(
        max_length=50, 
        default='fas fa-box',
        help_text="Font Awesome icon class (e.g., 'fas fa-hammer')"
    )
    color_class = models.CharField(
        max_length=20,
        default='primary',
        help_text="Bootstrap color class (e.g., 'primary', 'warning', 'info')"
    )
    display_order = models.PositiveIntegerField(
        default=0,
        help_text="Order in which categories are displayed (lower numbers first)"
    )
    featured = models.BooleanField(
        default=False,
        help_text="Display this category in featured sections"
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['display_order', 'name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('store:service_category', args=[self.slug])
    
    def get_service_category_url(self):
        """Get URL for service category pages"""
        if self.service_type:
            return reverse('store:service_category', args=[self.slug])
        return reverse('store:product_list_by_category', args=[self.slug])
    
    @property
    def product_count(self):
        """Return count of available products in this category"""
        return self.products.filter(available=True).count()
    
    @property
    def is_service_category(self):
        """Check if this is a main service category"""
        return bool(self.service_type)


class Product(models.Model):
    PRODUCT_TYPES = [
        ('material', 'Building Material'),
        ('tool', 'Construction Tool'),
        ('safety', 'Safety Equipment'),
        ('plumbing', 'Plumbing Item'),
        ('electrical', 'Electrical Item'),
        ('finishing', 'Finishing Material'),
        ('roofing', 'Roofing Material'),
    ]

    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, help_text="URL-friendly version of the name")
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    product_type = models.CharField(max_length=20, choices=PRODUCT_TYPES)
    image = CloudinaryField('product_image', folder='buildkit/products/')
    stock = models.PositiveIntegerField(default=0)
    available = models.BooleanField(default=True)
    featured = models.BooleanField(
        default=False,
        help_text="Feature this product on the homepage"
    )
    apply_price_increase = models.BooleanField(
        default=False,
        help_text="Apply 10% price increase when saving this product"
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-featured', '-created']
        indexes = [
            models.Index(fields=['category', 'available']),
            models.Index(fields=['product_type', 'available']),
            models.Index(fields=['featured', 'available']),
        ]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('store:product_detail', args=[self.slug])

    def clean(self):
        """Validate product data"""
        if self.price <= 0:
            raise ValidationError({'price': 'Price must be greater than zero'})
        if self.stock < 0:
            raise ValidationError({'stock': 'Stock cannot be negative'})

    def save(self, *args, **kwargs):
        # Apply 10% price increase if the option is selected
        if self.apply_price_increase and self.price:
            self.price = self.price * Decimal('1.10')
            # Reset the flag so it doesn't apply again on next save
            self.apply_price_increase = False
        
        self.full_clean()
        super().save(*args, **kwargs)

    def apply_ten_percent_increase(self):
        """Method to manually apply 10% price increase"""
        if self.price:
            self.price = self.price * Decimal('1.10')
            self.save()

    @property
    def price_with_increase(self):
        """Get the price with 10% increase without saving"""
        if self.price:
            return self.price * Decimal('1.10')
        return self.price

    @property
    def is_in_stock(self):
        return self.stock > 0 and self.available
    
    @property
    def low_stock(self):
        """Check if product has low stock (less than 10 items)"""
        return 0 < self.stock <= 10
    
    @property
    def stock_status(self):
        """Get stock status for display"""
        if not self.available:
            return "Unavailable"
        elif self.stock == 0:
            return "Out of Stock"
        elif self.low_stock:
            return f"Low Stock ({self.stock})"
        else:
            return f"In Stock ({self.stock})"
    
    @property
    def stock_status_class(self):
        """Get Bootstrap class for stock status"""
        if not self.available or self.stock == 0:
            return "danger"
        elif self.low_stock:
            return "warning"
        else:
            return "success"


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = CloudinaryField('product_gallery', folder='buildkit/products/gallery/')
    alt_text = models.CharField(max_length=100, blank=True, help_text="Alternative text for accessibility")
    is_primary = models.BooleanField(default=False, help_text="Use as main product image")
    display_order = models.PositiveIntegerField(
        default=0,
        help_text="Order in which images are displayed"
    )

    class Meta:
        ordering = ['-is_primary', 'display_order', 'id']

    def __str__(self):
        return f"Image for {self.product.name}"

    def save(self, *args, **kwargs):
        if not self.alt_text:
            self.alt_text = f"Image of {self.product.name}"
        
        # Ensure only one primary image per product
        if self.is_primary:
            ProductImage.objects.filter(
                product=self.product, 
                is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)
        
        super().save(*args, **kwargs)


class Testimonial(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='testimonials')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    reviewer_name = models.CharField(max_length=100)
    rating = models.PositiveIntegerField(
        choices=[(i, f'{i} Star{"s" if i != 1 else ""}') for i in range(1, 6)], 
        default=5
    )
    content = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    approved = models.BooleanField(default=False)
    featured = models.BooleanField(
        default=False,
        help_text="Feature this testimonial on product pages"
    )

    class Meta:
        ordering = ['-featured', '-created']
        unique_together = ['product', 'user']

    def __str__(self):
        return f"Testimonial for {self.product.name} by {self.reviewer_name}"

    def clean(self):
        if self.rating < 1 or self.rating > 5:
            raise ValidationError({'rating': 'Rating must be between 1 and 5'})
        if len(self.content.strip()) < 10:
            raise ValidationError({'content': 'Review must be at least 10 characters long'})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    DELIVERY_METHODS = [
        ('free', 'Free Delivery'),
        ('flat', 'Flat Rate Delivery'),
        ('express', 'Express Delivery'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20, blank=True)
    region = models.CharField(max_length=100)
    address = models.CharField(max_length=250)
    postal_code = models.CharField(max_length=20, blank=True)
    city = models.CharField(max_length=100)
    delivery_method = models.CharField(max_length=10, choices=DELIVERY_METHODS, default='free')
    delivery_cost = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    paid = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True, help_text="Additional order notes")

    class Meta:
        ordering = ['-created']
        indexes = [
            models.Index(fields=['user', 'created']),
            models.Index(fields=['status', 'created']),
            models.Index(fields=['paid', 'created']),
        ]

    def __str__(self):
        return f'Order {self.id} - {self.full_name}'

    def get_total_cost(self):
        items_total = sum(item.get_cost() for item in self.items.all())
        return items_total + self.delivery_cost

    def get_total_cost_display(self):
        return f"₵{self.get_total_cost():.2f}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def items_count(self):
        return sum(item.quantity for item in self.items.all())
    
    @property
    def status_class(self):
        """Get Bootstrap class for order status"""
        status_classes = {
            'pending': 'warning',
            'confirmed': 'info',
            'processing': 'primary',
            'shipped': 'success',
            'delivered': 'dark',
            'cancelled': 'danger',
        }
        return status_classes.get(self.status, 'secondary')

    def clean(self):
        if self.delivery_cost < 0:
            raise ValidationError({'delivery_cost': 'Delivery cost cannot be negative'})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    
    class Meta:
        unique_together = ['order', 'product']

    def __str__(self):
        return f'{self.quantity} x {self.product.name} (Order {self.order.id})'
    
    def get_cost(self):
        return self.price * self.quantity

    def get_cost_display(self):
        return f"₵{self.get_cost():.2f}"

    def clean(self):
        if self.quantity <= 0:
            raise ValidationError({'quantity': 'Quantity must be greater than zero'})
        if self.price <= 0:
            raise ValidationError({'price': 'Price must be greater than zero'})

    def save(self, *args, **kwargs):
        if not self.price:
            # Get the current product price
            self.price = self.product.price
        self.full_clean()
        super().save(*args, **kwargs)