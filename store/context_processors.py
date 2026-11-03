from .cart import Cart
from .models import Category


def cart_and_categories(request):
    """
    Globally available context variables:
    - categories: All product categories for header navigation
    - cart: Shopping cart instance
    - cart_item_count: Total item count badge
    - cart_subtotal: Cart subtotal amount in INR
    - is_admin_user: Whether logged-in user is staff/superuser
    """
    cart = Cart(request)
    categories = Category.objects.all().order_by('name')

    return {
        'cart': cart,
        'cart_item_count': len(cart),
        'cart_subtotal': cart.subtotal,
        'cart_total_amount': cart.total_amount,
        'all_categories': categories,
        'is_admin_user': request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser),
    }
