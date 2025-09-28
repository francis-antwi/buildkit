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
        null=True,       # allow NULL in DB
        blank=True,      # allow empty form field
        help_text="Enter phone number in format +1234567890"
    )

    def clean(self):
        """Validate phone number format"""
        if self.phone_number and self.phone_number.strip():
            # Remove any whitespace
            self.phone_number = self.phone_number.strip()
            
            # Basic validation for international format
            if not re.match(r'^\+\d{1,3}\d{6,12}$', self.phone_number):
                raise ValidationError({
                    'phone_number': 'Phone number must be in international format (e.g., +233598670304)'
                })
        else:
            # If empty or whitespace only, set to None
            self.phone_number = None

    def save(self, *args, **kwargs):
        # Convert empty strings and whitespace to None to avoid unique constraint issues
        if not self.phone_number or self.phone_number.strip() == '':
            self.phone_number = None
        else:
            # Clean up whitespace
            self.phone_number = self.phone_number.strip()
        
        # Run model validation
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Profile for {self.user.username}"

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, help_text="URL-friendly version of the name")
    description = models.TextField(blank=True)
    image = CloudinaryField('category_image', folder='buildkit/categories/', blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('store:category_detail', args=[self.slug])


class Product(models.Model):
    PRODUCT_TYPES = [
        ('material', 'Building Material'),
        ('tool', 'Construction Tool'),
        ('safety', 'Safety Equipment'),
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
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created']
        indexes = [
            models.Index(fields=['category', 'available']),
            models.Index(fields=['product_type', 'available']),
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
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def is_in_stock(self):
        return self.stock > 0 and self.available


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = CloudinaryField('product_gallery', folder='buildkit/products/gallery/')
    alt_text = models.CharField(max_length=100, blank=True, help_text="Alternative text for accessibility")
    is_primary = models.BooleanField(default=False, help_text="Use as main product image")

    class Meta:
        ordering = ['-is_primary', 'id']

    def __str__(self):
        return f"Image for {self.product.name}"

    def save(self, *args, **kwargs):
        # Auto-generate alt_text if not provided
        if not self.alt_text:
            self.alt_text = f"Image of {self.product.name}"
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

    class Meta:
        ordering = ['-created']
        unique_together = ['product', 'user']  # Prevent duplicate reviews from same user

    def __str__(self):
        return f"Testimonial for {self.product.name} by {self.reviewer_name}"

    def clean(self):
        """Validate testimonial data"""
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
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    DELIVERY_METHODS = [
        ('free', 'Free Delivery'),
        ('flat', 'Flat Rate Delivery'),
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

    class Meta:
        ordering = ['-created']
        indexes = [
            models.Index(fields=['user', 'created']),
            models.Index(fields=['status', 'created']),
        ]

    def __str__(self):
        return f'Order {self.id}'

    def get_total_cost(self):
        """Calculate total order cost including delivery"""
        items_total = sum(item.get_cost() for item in self.items.all())
        total = items_total + self.delivery_cost
        return total

    def get_total_cost_display(self):
        """Get formatted total cost"""
        return f"${self.get_total_cost():.2f}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def clean(self):
        """Validate order data"""
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
        unique_together = ['order', 'product']  # Prevent duplicate items in same order

    def __str__(self):
        return f'{self.quantity} x {self.product.name} (Order {self.order.id})'
    
    def get_cost(self):
        """Calculate total cost for this item"""
        return self.price * self.quantity

    def get_cost_display(self):
        """Get formatted cost"""
        return f"${self.get_cost():.2f}"

    def clean(self):
        """Validate order item data"""
        if self.quantity <= 0:
            raise ValidationError({'quantity': 'Quantity must be greater than zero'})
        
        if self.price <= 0:
            raise ValidationError({'price': 'Price must be greater than zero'})

    def save(self, *args, **kwargs):
        # Set price from product if not specified
        if not self.price:
            self.price = self.product.price
        
        self.full_clean()
        super().save(*args, **kwargs)