from django.contrib import admin
from .models import UserProfile, Category, Product, ProductImage, Testimonial, Order, OrderItem
from cart.forms import UserProfileForm


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    form = UserProfileForm
    list_display = ['user', 'phone_number']
    list_filter = ['user__date_joined']
    search_fields = ['user__username', 'user__email', 'phone_number']
    raw_id_fields = ['user']


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ['image', 'alt_text', 'is_primary']


class TestimonialInline(admin.TabularInline):
    model = Testimonial
    extra = 0
    fields = ['reviewer_name', 'rating', 'content', 'approved']
    readonly_fields = ['created']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'created']
    list_filter = ['created']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'product_type', 'price', 'stock', 'available', 'created']
    list_filter = ['available', 'category', 'product_type', 'created']
    list_editable = ['price', 'stock', 'available']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline, TestimonialInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description', 'category', 'product_type')
        }),
        ('Pricing & Stock', {
            'fields': ('price', 'stock', 'available')
        }),
        ('Media', {
            'fields': ('image',)
        }),
    )


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ['product', 'reviewer_name', 'rating', 'approved', 'created']
    list_filter = ['rating', 'approved', 'created']
    search_fields = ['reviewer_name', 'content', 'product__name']
    actions = ['approve_testimonials', 'disapprove_testimonials']

    def approve_testimonials(self, request, queryset):
        queryset.update(approved=True)
    approve_testimonials.short_description = "Approve selected testimonials"

    def disapprove_testimonials(self, request, queryset):
        queryset.update(approved=False)
    disapprove_testimonials.short_description = "Disapprove selected testimonials"


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    raw_id_fields = ['product']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'full_name', 'email', 'city', 'status', 'paid', 'created']
    list_filter = ['status', 'paid', 'delivery_method', 'created']
    search_fields = ['first_name', 'last_name', 'email', 'city']
    list_editable = ['status', 'paid']
    inlines = [OrderItemInline]
    
    fieldsets = (
        ('Customer Information', {
            'fields': ('user', 'first_name', 'last_name', 'email', 'phone_number')
        }),
        ('Delivery Information', {
            'fields': ('region', 'city', 'address', 'postal_code', 'delivery_method', 'delivery_cost')
        }),
        ('Order Status', {
            'fields': ('status', 'paid')
        }),
    )

    readonly_fields = ['created', 'updated']