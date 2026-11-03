from decimal import Decimal
from django.db import transaction
from .models import Cart as CartModel, CartItem, Product


class Cart:
    """
    Unified Database & Session Cart Manager for ShopKart India.
    Supports guest sessions and merges seamlessly into user accounts upon login.
    """
    def __init__(self, request):
        self.request = request
        self.user = request.user if request.user.is_authenticated else None

        # Ensure session exists for guest tracking
        if not request.session.session_key:
            request.session.create()
        self.session_key = request.session.session_key

        self.cart_obj = self._get_or_create_cart()

    def _get_or_create_cart(self):
        """
        Retrieves or creates a database Cart record for the user or guest session.
        If user is logged in, merges any unassigned guest cart into the user's cart.
        """
        if self.user:
            cart, created = CartModel.objects.get_or_create(user=self.user)
            # Merge any orphan guest session items if they exist
            if self.session_key:
                guest_cart = CartModel.objects.filter(session_key=self.session_key, user__isnull=True).first()
                if guest_cart and guest_cart.id != cart.id:
                    for g_item in guest_cart.items.all():
                        item, item_created = CartItem.objects.get_or_create(
                            cart=cart,
                            product=g_item.product,
                            defaults={'quantity': g_item.quantity}
                        )
                        if not item_created:
                            item.quantity += g_item.quantity
                            if item.quantity > g_item.product.stock:
                                item.quantity = g_item.product.stock
                            item.save()
                    guest_cart.delete()
            return cart
        else:
            cart, created = CartModel.objects.get_or_create(
                session_key=self.session_key,
                user__isnull=True
            )
            return cart

    def add(self, product, quantity=1, override_quantity=False):
        """
        Add a product to cart or increment its quantity.
        Validates against current product inventory.
        """
        if product.stock <= 0:
            return False, f"Sorry, '{product.name}' is currently out of stock."

        item, created = CartItem.objects.get_or_create(
            cart=self.cart_obj,
            product=product,
            defaults={'quantity': quantity}
        )

        if not created:
            if override_quantity:
                new_qty = quantity
            else:
                new_qty = item.quantity + quantity

            if new_qty > product.stock:
                new_qty = product.stock

            if new_qty <= 0:
                item.delete()
                return True, "Item removed from cart."

            item.quantity = new_qty
            item.save()

        # Update session touch
        self.request.session.modified = True
        return True, f"'{product.name}' added to your cart."

    def decrease(self, product):
        """
        Decrease quantity by 1. Removes item if quantity reaches 0.
        """
        item = CartItem.objects.filter(cart=self.cart_obj, product=product).first()
        if item:
            if item.quantity > 1:
                item.quantity -= 1
                item.save()
            else:
                item.delete()
            self.request.session.modified = True

    def remove(self, product):
        """
        Remove a product completely from the cart.
        """
        CartItem.objects.filter(cart=self.cart_obj, product=product).delete()
        self.request.session.modified = True

    def clear(self):
        """
        Clear all items from the cart.
        """
        self.cart_obj.items.all().delete()
        self.request.session.modified = True

    def __iter__(self):
        """
        Iterate over cart items.
        """
        items = self.cart_obj.items.select_related('product', 'product__category').all()
        for item in items:
            yield {
                'product': item.product,
                'product_id': item.product.id,
                'name': item.product.name,
                'category': item.product.category.name,
                'price': item.product.selling_price,
                'mrp': item.product.mrp,
                'discount_percent': item.product.discount_percent,
                'savings': (item.product.mrp - item.product.selling_price) * item.quantity,
                'quantity': item.quantity,
                'stock': item.product.stock,
                'image': item.product.image_url,
                'subtotal': item.subtotal,
                'is_available': item.product.stock >= item.quantity,
            }

    def __len__(self):
        """
        Total quantity of all items in the cart.
        """
        return sum(item.quantity for item in self.cart_obj.items.all())

    @property
    def subtotal(self):
        """
        Total subtotal of items in cart.
        """
        return sum(item.subtotal for item in self.cart_obj.items.select_related('product').all())

    @property
    def delivery_charge(self):
        """
        Free delivery on orders >= ₹999; otherwise ₹49.
        """
        if self.subtotal >= Decimal('999.00') or len(self) == 0:
            return Decimal('0.00')
        return Decimal('49.00')

    @property
    def gst_amount(self):
        """
        18% GST calculation.
        """
        return round(self.subtotal * Decimal('0.18'), 2)

    @property
    def total_amount(self):
        """
        Subtotal + delivery charge.
        """
        return self.subtotal + self.delivery_charge

    @property
    def total_savings(self):
        """
        Total discount saved on MRP.
        """
        savings = Decimal('0.00')
        for item in self.cart_obj.items.select_related('product').all():
            if item.product.mrp > item.product.selling_price:
                savings += (item.product.mrp - item.product.selling_price) * item.quantity
        return savings

    def get_cart_data(self):
        """
        JSON-serializable representation of the cart for frontend AJAX and localStorage sync.
        """
        items_list = []
        for item in self:
            items_list.append({
                'product_id': item['product_id'],
                'name': item['name'],
                'category': item['category'],
                'price': float(item['price']),
                'mrp': float(item['mrp']),
                'quantity': item['quantity'],
                'stock': item['stock'],
                'image': item['image'],
                'subtotal': float(item['subtotal']),
            })

        return {
            'items': items_list,
            'total_count': len(self),
            'subtotal': float(self.subtotal),
            'delivery_charge': float(self.delivery_charge),
            'gst_amount': float(self.gst_amount),
            'total_amount': float(self.total_amount),
            'total_savings': float(self.total_savings),
        }
