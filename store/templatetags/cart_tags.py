from django import template

register = template.Library()

@register.filter
def lookup(cart, product_id):
    product_id = str(product_id)
    return cart.cart.get(product_id, {}).get('quantity', 0)