from django.urls import path
from . import views

app_name = 'cart'
urlpatterns = [
    path('add/<int:product_id>/', views.cart_add, name='cart_add'),
    path('remove/<int:product_id>/', views.cart_remove, name='cart_remove'),
    path('', views.cart_detail, name='cart_detail'),
    path('calculate-delivery/', views.calculate_delivery, name='calculate_delivery'),
    path('checkout/', views.checkout, name='checkout'),
    path('checkout/whatsapp/', views.checkout_whatsapp, name='checkout_whatsapp'),
    path('order-confirmation/', views.order_confirmation, name='order_confirmation'),
]