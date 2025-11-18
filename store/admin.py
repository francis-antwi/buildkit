from django.contrib import admin
from django.utils.html import format_html
from .models import (
    UserProfile, Category, Product, ProductImage, 
    Testimonial, Order, OrderItem, TechnicalSpecification, SpecificationGroup
)


class TechnicalSpecificationInline(admin.TabularInline):
    model = TechnicalSpecification
    extra = 1
    fields = ['spec_name', 'spec_value', 'spec_unit', 'group', 'display_order', 'is_important']
    ordering = ['group', 'display_order']


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ['image', 'alt_text', 'is_primary', 'display_order']


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone_number']
    search_fields = ['user__username', 'user__email', 'phone_number']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'service_type', 'display_order', 'featured', 'product_count']
    list_filter = ['service_type', 'featured']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['display_order', 'featured']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'category', 'product_type', 'price', 'stock', 
        'available', 'has_technical_specs', 'technical_data_link'
    ]
    list_filter = [
        'category', 'available', 'has_technical_specs', 
        'product_type', 'featured'
    ]
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [TechnicalSpecificationInline, ProductImageInline]
    readonly_fields = ['has_technical_specs']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description', 'category', 'product_type')
        }),
        ('Pricing & Inventory', {
            'fields': ('price', 'apply_price_increase', 'stock', 'available')
        }),
        ('Media', {
            'fields': ('image', 'featured')
        }),
        ('Technical Data', {
            'fields': ('has_technical_specs', 'technical_data_sheet'),
            'classes': ('collapse',)
        }),
    )

    def technical_data_link(self, obj):
        if obj.technical_data_sheet:
            return format_html(
                '<a href="{}" target="_blank">📄 View TDS</a>',
                obj.technical_data_sheet.url
            )
        return "No TDS"
    technical_data_link.short_description = 'Technical Data Sheet'


@admin.register(TechnicalSpecification)
class TechnicalSpecificationAdmin(admin.ModelAdmin):
    list_display = ['product', 'spec_name', 'spec_value', 'spec_unit', 'group', 'is_important']
    list_filter = ['group', 'is_important', 'product__category']
    search_fields = ['product__name', 'spec_name', 'spec_value']
    list_editable = ['spec_value', 'spec_unit', 'is_important']


@admin.register(SpecificationGroup)
class SpecificationGroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'display_name', 'display_order', 'icon_class']
    ordering = ['display_order']
    list_editable = ['display_order']


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['product', 'image_preview', 'is_primary', 'display_order']
    list_filter = ['is_primary', 'product__category']
    search_fields = ['product__name', 'alt_text']
    
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width: 50px; height: 50px; object-fit: cover;" />',
                obj.image.url
            )
        return "No Image"
    image_preview.short_description = 'Preview'


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ['product', 'reviewer_name', 'rating', 'approved', 'featured', 'created']
    list_filter = ['rating', 'approved', 'featured', 'created']
    search_fields = ['product__name', 'reviewer_name', 'content']
    list_editable = ['approved', 'featured']


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['product']
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'full_name', 'email', 'phone_number', 
        'get_total_cost', 'paid', 'status', 'created'
    ]
    list_filter = ['paid', 'status', 'created', 'delivery_method']
    search_fields = ['first_name', 'last_name', 'email', 'phone_number']
    inlines = [OrderItemInline]
    readonly_fields = ['created', 'updated']
    
    def get_total_cost(self, obj):
        return f"₵{obj.get_total_cost():.2f}"
    get_total_cost.short_description = 'Total Cost'


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product', 'price', 'quantity', 'get_cost']
    list_filter = ['order__status', 'order__created']
    search_fields = ['order__id', 'product__name']
    
    def get_cost(self, obj):
        return f"₵{obj.get_cost():.2f}"
    get_cost.short_description = 'Total Cost'