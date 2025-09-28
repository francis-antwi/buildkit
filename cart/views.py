from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from store.models import Product,Order, OrderItem
from .cart import Cart
from .forms import CartAddProductForm, DeliveryCalculatorForm
from urllib.parse import quote
from django.contrib.auth.models import User
from store.models import UserProfile
from decimal import Decimal
from django.conf import settings


@require_POST
def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    form = CartAddProductForm(request.POST)
    print(f"POST data for product {product_id}: {request.POST}")  # Debugging
    if form.is_valid():
        cd = form.cleaned_data
        print(f"Form cleaned data: {cd}")  # Debugging
        cart.add(product=product, quantity=cd['quantity'], override_quantity=cd['override'])
        print(f"Cart after add: {cart.cart}")  # Debugging
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'quantity': cart.cart.get(str(product_id), {}).get('quantity', 0)
            })
    else:
        print(f"Form errors: {form.errors}")  # Debugging
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': form.errors.as_json()}, status=400)
    return redirect('cart:cart_detail')

@require_POST
def cart_remove(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    return redirect('cart:cart_detail')
def checkout(request):
    cart = Cart(request)
    if not cart:
        return redirect('cart:cart_detail')

    if request.user.is_authenticated:
        # Ensure a profile exists for this user
        profile, created = UserProfile.objects.get_or_create(user=request.user)

        first_name = request.user.first_name or request.user.username
        last_name = request.user.last_name or ''
        email = request.user.email or ''
        phone_number = profile.phone_number or ''
    else:
        first_name = request.session.get('first_name', '')
        last_name = request.session.get('last_name', '')
        email = request.session.get('email', '')
        phone_number = request.session.get('phone_number', '')

    # Use the correct session keys that match what's set in calculate_delivery
    context = {
    'cart': cart,
    'delivery_country': request.session.get('delivery_country', 'GH'),
    'region': request.session.get('region', ''),
    'address': request.session.get('address', ''),
    'city': request.session.get('city', ''),
    'postal_code': request.session.get('postal_code', ''),  # optional
    'delivery_method': request.session.get('delivery_method', 'free'),
    'delivery_cost': request.session.get('delivery_cost', 0.00),
    'first_name': first_name,
    'last_name': last_name,   # optional
    'email': email,
    'phone_number': phone_number,
}

    
    # Debug: Print session data to console
    print("Session data in checkout view:")
    print(f"Region: {request.session.get('region')}")
    print(f"Address: {request.session.get('address')}")
    print(f"City: {request.session.get('city')}")
    print(f"Postal Code: {request.session.get('postal_code')}")
    print(f"Delivery Method: {request.session.get('delivery_method')}")
    
    return render(request, 'cart/checkout.html', context)

def cart_detail(request):
    cart = Cart(request)
    
    for item in cart:
        item['update_quantity_form'] = CartAddProductForm(initial={
            'quantity': item['quantity'],
            'override': True
        })
    
    context = {
        'cart': cart,
        'region': request.session.get('region', ''),
        'address': request.session.get('address', ''),
        'city': request.session.get('city', ''),
        'postal_code': request.session.get('postal_code', ''),
        'delivery_method': request.session.get('delivery_method', 'free'),
        'delivery_cost': request.session.get('delivery_cost', 0.00),
        'first_name': request.session.get('first_name', ''),
        'last_name': request.session.get('last_name', ''),
        'email': request.session.get('email', ''),
        'phone_number': request.session.get('phone_number', ''),
    }
    
    return render(request, 'cart/detail.html', context)

@require_POST
def calculate_delivery(request):
    cart = Cart(request)
    
    form = DeliveryCalculatorForm(request.POST, user_is_authenticated=request.user.is_authenticated)
    if not form.is_valid():
        return redirect('cart:cart_detail')
    
    cd = form.cleaned_data
    
    # ✅ Always cast values before saving into session
    request.session['delivery_country'] = str(cd['calc_delivery_country'])
    request.session['region'] = str(cd['region'])
    request.session['address'] = str(cd['address'])
    request.session['city'] = str(cd['city'])
    request.session['postal_code'] = str(cd['postal_code'])
    request.session['delivery_method'] = str(cd['delivery_method'])
    request.session['delivery_cost'] = 100.00 if cd['delivery_method'] == 'flat' else 0.00


    if not request.user.is_authenticated:
        request.session['first_name'] = str(cd['first_name'])
        request.session['last_name'] = str(cd['last_name'])
        request.session['email'] = str(cd['email'])
        request.session['phone_number'] = str(cd['phone_number'])
    
    request.session.modified = True
    return redirect('cart:cart_detail')
    
def checkout_whatsapp(request):
    from decimal import Decimal
    from urllib.parse import quote
    from django.shortcuts import redirect
    from django.conf import settings
    
    print("=== CHECKOUT WHATSAPP STARTED ===")
    
    # Initialize cart
    try:
        cart = Cart(request)
        print(f"Cart initialized successfully. Items: {len(cart)}")
    except Exception as e:
        print(f"Error initializing cart: {e}")
        return redirect('cart:cart_detail')
    
    if not cart:
        print("REDIRECT: Cart is empty")
        return redirect('cart:cart_detail')

    # User details
    if request.user.is_authenticated:
        first_name = request.user.first_name or request.user.username or 'Customer'
        last_name = request.user.last_name or 'User'
        email = request.user.email or 'no-email@example.com'
        phone_number = getattr(request.user.profile, 'phone_number', 'Not specified') if hasattr(request.user, 'profile') else 'Not specified'
    else:
        first_name = request.session.get('first_name', 'Customer')
        last_name = request.session.get('last_name', 'User')
        email = request.session.get('email', 'no-email@example.com')
        phone_number = request.session.get('phone_number', 'Not specified')

    # Delivery details - Convert all to appropriate types
    region = request.session.get('region')
    address = request.session.get('address')
    city = request.session.get('city')
    postal_code = request.session.get('postal_code', 'Not specified')
    delivery_method = request.session.get('delivery_method', 'free')
    
    # Handle delivery_cost more carefully
    delivery_cost_raw = request.session.get('delivery_cost', 0)
    try:
        if isinstance(delivery_cost_raw, Decimal):
            delivery_cost = float(delivery_cost_raw)
        else:
            delivery_cost = float(delivery_cost_raw)
    except (ValueError, TypeError):
        delivery_cost = 0.0

    # Validate required fields
    required_fields = {
        'first_name': first_name,
        'last_name': last_name, 
        'email': email,
        'address': address,
        'city': city,
        'region': region
    }
    missing_fields = [field for field, value in required_fields.items() if not value]
    if missing_fields or (not request.user.is_authenticated and not phone_number):
        print(f"REDIRECT: Missing required fields: {missing_fields}")
        return redirect('cart:cart_detail')

    print("All validations passed, creating order...")
    
    # Create order
    try:
        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone_number=phone_number,
            region=region,
            address=address,
            city=city,
            postal_code=postal_code,
            delivery_method=delivery_method,
            delivery_cost=Decimal(str(delivery_cost)),
            paid=False,
            status='pending'
        )
        print(f"Order created: #{order.id}")
    except Exception as e:
        print(f"Error creating order: {e}")
        return redirect('cart:cart_detail')

    # Create order items
    try:
        for item in cart:
            item_price = item['price']
            if not isinstance(item_price, Decimal):
                item_price = Decimal(str(item_price))
                
            OrderItem.objects.create(
                order=order,
                product=item['product'],
                price=item_price,
                quantity=item['quantity']
            )
        print("Order items created successfully")
    except Exception as e:
        print(f"Error creating order items: {e}")
        order.delete()
        return redirect('cart:cart_detail')

    # Build invoice message - Convert all Decimals to basic types
    message_parts = []
    message_parts.append(f"Order Invoice #{int(order.id)}")
    message_parts.append("")
    message_parts.append("--- Customer Details ---")
    message_parts.append(f"Name: {str(first_name)} {str(last_name)}")
    message_parts.append(f"Email: {str(email)}")
    message_parts.append(f"Phone: {str(phone_number)}")
    message_parts.append("")
    message_parts.append("--- Order Details ---")
    
    for item in cart:
        product_name = str(item['product'].name)
        quantity = int(item['quantity'])
        price = float(item['price']) if isinstance(item['price'], Decimal) else float(item['price'])
        total_price = float(item['total_price']) if isinstance(item['total_price'], Decimal) else float(item['total_price'])
        
        message_parts.append(f"Product: {product_name}")
        message_parts.append(f"Quantity: {quantity}")
        message_parts.append(f"Price: GHS {price:.2f}")
        message_parts.append(f"Total: GHS {total_price:.2f}")
        message_parts.append("")
    
    message_parts.append("--- Cart Totals ---")
    
    # Convert totals to float
    cart_total_raw = cart.get_total_price()
    cart_total = float(cart_total_raw) if isinstance(cart_total_raw, Decimal) else float(cart_total_raw)
    
    order_total_raw = order.get_total_cost()
    order_total = float(order_total_raw) if isinstance(order_total_raw, Decimal) else float(order_total_raw)
    
    message_parts.append(f"Subtotal: GHS {cart_total:.2f}")
    message_parts.append(f"Delivery: GHS {delivery_cost:.2f}")
    message_parts.append(f"Total: GHS {order_total:.2f}")
    message_parts.append("")
    message_parts.append("--- Delivery Details ---")
    message_parts.append(f"Region: {str(region)}")
    message_parts.append(f"Address: {str(address)}")
    message_parts.append(f"City: {str(city)}")
    message_parts.append(f"Postal Code: {str(postal_code)}")
    message_parts.append("Country: Ghana")
    message_parts.append(f"Delivery Method: {str(delivery_method).title()}")
    
    message = "\n".join(message_parts)

    # CRITICAL FIX: Clear cart and all session data that might contain Decimals
    print("=== CLEARING CART AND SESSION DATA ===")
    
    # Method 1: Try to clear cart normally first
    try:
        cart.clear()
        print("Cart cleared using cart.clear()")
    except Exception as e:
        print(f"Error with cart.clear(): {e}")
    
    # Method 2: Force clear cart session data directly
    cart_session_key = getattr(cart, 'session_key', 'cart')  # Usually 'cart'
    if cart_session_key in request.session:
        try:
            del request.session[cart_session_key]
            print(f"Force deleted cart session key: {cart_session_key}")
        except KeyError:
            pass
    
    # Method 3: Remove ALL session keys that might contain cart data or Decimals
    session_keys_to_remove = [
        'delivery_country', 'region', 'address', 'city', 'postal_code', 
        'delivery_method', 'delivery_cost', 'first_name', 'last_name', 
        'email', 'phone_number', 'cart', '_cart', 'whatsapp_url', 'order_id'
    ]
    
    # Get all session keys and remove problematic ones
    all_session_keys = list(request.session.keys())
    for key in all_session_keys:
        if (key in session_keys_to_remove or 
            key.startswith('cart') or 
            key.startswith('_cart') or
            'cart' in key.lower()):
            try:
                del request.session[key]
                print(f"Removed session key: {key}")
            except KeyError:
                pass
    
    # Force session modification and save
    request.session.modified = True
    
    # Try to save the cleaned session
    try:
        request.session.save()
        print("Session cleaned and saved successfully")
    except Exception as e:
        print(f"Error saving cleaned session: {e}")
        # If session save fails due to Decimals, flush everything
        try:
            request.session.flush()
            print("Session completely flushed due to save error")
        except Exception as flush_error:
            print(f"Error flushing session: {flush_error}")
    
    # Verify cart is empty by creating a new cart instance
    try:
        verification_cart = Cart(request)
        print(f"Cart verification - Items remaining: {len(verification_cart)}")
        if len(verification_cart) > 0:
            print("WARNING: Cart still contains items after clearing!")
            # Force clear again
            verification_cart.clear()
            request.session.modified = True
    except Exception as e:
        print(f"Error verifying cart clear: {e}")

    # WhatsApp URL
    whatsapp_number = getattr(settings, 'WHATSAPP_ADMIN_NUMBER', '+233501234567')
    whatsapp_url = f"https://wa.me/{whatsapp_number}?text={quote(message)}"

    # Store ONLY basic Python types in session
    print("=== STORING CLEAN DATA IN SESSION ===")
    try:
        # Ensure we're only storing JSON-serializable types
        request.session['whatsapp_url'] = str(whatsapp_url)
        request.session['order_id'] = int(order.id)
        request.session.modified = True
        
        # Test session save
        request.session.save()
        print("Clean session data stored and saved successfully")
    except Exception as e:
        print(f"Error storing clean session data: {e}")
        # Fallback: pass data via URL parameters instead of session
        from django.urls import reverse
        from urllib.parse import urlencode
        
        params = urlencode({
            'order_id': int(order.id),
            'whatsapp_url': whatsapp_url
        })
        return redirect(f"{reverse('cart:order_confirmation')}?{params}")
    
    print("=== CHECKOUT WHATSAPP COMPLETED ===")
    return redirect('cart:order_confirmation')
def order_confirmation(request):
    whatsapp_url = request.session.get('whatsapp_url')
    order_id = request.session.get('order_id')
    
    if not whatsapp_url:
        return redirect('cart:cart_detail')
    
    context = {
        'whatsapp_url': whatsapp_url,
        'order_id': order_id,
    }
    
    # Clear the session data after displaying
    request.session.pop('whatsapp_url', None)
    request.session.pop('order_id', None)
    request.session.modified = True
    
    return render(request, 'cart/order_confirmation.html', context)