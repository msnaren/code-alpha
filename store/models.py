import random
from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.text import slugify
from django.utils import timezone
from datetime import timedelta


class Category(models.Model):
    """
    Product Category model representing Indian e-commerce departments
    such as Electronics, Fashion, Home & Kitchen, Beauty, Books, Grocery.
    """
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Product(models.Model):
    """
    Product Model representing items for sale on ShopKart India.
    Supports MRP, selling price in ₹, ratings, stock status, and featured tags.
    """
    name = models.CharField(max_length=250, db_index=True)
    slug = models.SlugField(max_length=260, unique=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    description = models.TextField()
    image = models.CharField(
        max_length=500,
        blank=True,
        default='',
        help_text="URL or static path to product image"
    )
    mrp = models.DecimalField(max_digits=10, decimal_places=2, help_text="Maximum Retail Price in INR")
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Discounted selling price in INR")
    stock = models.PositiveIntegerField(default=0)
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=Decimal('4.5'))
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} (₹{self.selling_price})"

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Product.objects.filter(slug=slug).exclude(id=self.id).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('product_detail', args=[self.id])

    @property
    def price(self):
        """Alias for compatibility with views/cart calculations."""
        return self.selling_price

    @property
    def is_in_stock(self):
        return self.stock > 0

    @property
    def discount_percent(self):
        if self.mrp and self.mrp > 0 and self.selling_price < self.mrp:
            return int(round(((self.mrp - self.selling_price) / self.mrp) * 100))
        return 0

    @property
    def savings(self):
        if self.mrp and self.selling_price < self.mrp:
            return self.mrp - self.selling_price
        return Decimal('0.00')

    @property
    def short_description(self):
        if len(self.description) > 95:
            return self.description[:95] + '...'
        return self.description

    @property
    def image_url(self):
        if self.image:
            return self.image
        return '/static/images/placeholder.svg'


class UserProfile(models.Model):
    """
    Extends standard Django User with Indian shipping details:
    10-digit mobile number, address, city, state, and 6-digit PIN code.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    mobile = models.CharField(max_length=15, blank=True, default='')
    address = models.CharField(max_length=255, blank=True, default='')
    city = models.CharField(max_length=100, blank=True, default='')
    state = models.CharField(max_length=100, blank=True, default='')
    pin_code = models.CharField(max_length=6, blank=True, default='')

    def __str__(self):
        return f"Profile of {self.user.username} ({self.mobile})"


class Cart(models.Model):
    """
    Database-backed Shopping Cart for persistent cart management across sessions.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='carts')
    session_key = models.CharField(max_length=40, null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart #{self.id} (User: {self.user or 'Guest'}, Items: {self.total_count})"

    @property
    def total_count(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def subtotal(self):
        return sum(item.subtotal for item in self.items.all())

    @property
    def delivery_charge(self):
        # Free delivery for orders above ₹999, else ₹49
        if self.subtotal >= Decimal('999.00') or self.total_count == 0:
            return Decimal('0.00')
        return Decimal('49.00')

    @property
    def amount_for_free_delivery(self):
        if self.subtotal < Decimal('999.00'):
            return Decimal('999.00') - self.subtotal
        return Decimal('0.00')

    @property
    def gst_amount(self):
        # 18% GST calculation
        return round(self.subtotal * Decimal('0.18'), 2)

    @property
    def total_amount(self):
        return self.subtotal + self.delivery_charge


class CartItem(models.Model):
    """
    Individual items inside a persistent Cart.
    """
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('cart', 'product')
        ordering = ['-added_date']

    def __str__(self):
        return f"{self.quantity}x {self.product.name} in Cart #{self.cart_id}"

    @property
    def subtotal(self):
        return self.quantity * self.product.selling_price


class Order(models.Model):
    """
    Order Model tracking purchases placed on ShopKart India.
    Includes unique order number format (SK-2026-XXXX), delivery address,
    Indian phone number, 6-digit PIN, payment method, GST, and delivery charges.
    """
    STATUS_CHOICES = [
        ('Placed', 'Order Placed'),
        ('Processing', 'Processing'),
        ('Shipped', 'Shipped'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
    ]

    PAYMENT_CHOICES = [
        ('Cash on Delivery', 'Cash on Delivery (COD)'),
        ('UPI', 'UPI / QR Payment (GPay, PhonePe, Paytm)'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    order_number = models.CharField(max_length=30, unique=True, editable=False, db_index=True)
    full_name = models.CharField(max_length=150)
    mobile = models.CharField(max_length=15)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pin_code = models.CharField(max_length=6)
    payment_method = models.CharField(max_length=50, choices=PAYMENT_CHOICES, default='Cash on Delivery')

    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    delivery_charge = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    gst_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default='Placed')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.order_number} - {self.full_name} (₹{self.total_amount})"

    def save(self, *args, **kwargs):
        if not self.order_number:
            year = timezone.now().year
            rand_suffix = random.randint(1000, 9999)
            base_number = f"SK-{year}-{rand_suffix}"
            while Order.objects.filter(order_number=base_number).exists():
                rand_suffix = random.randint(1000, 9999)
                base_number = f"SK-{year}-{rand_suffix}"
            self.order_number = base_number
        super().save(*args, **kwargs)

    @property
    def item_count(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def estimated_delivery_date(self):
        # 3 to 4 business days from created_at
        return self.created_at + timedelta(days=4)


class OrderItem(models.Model):
    """
    Individual items captured within an Order at the time of purchase.
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, related_name='order_items')
    product_name = models.CharField(max_length=250)
    price_at_purchase = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity}x {self.product_name} @ ₹{self.price_at_purchase}"

    @property
    def subtotal(self):
        return self.quantity * self.price_at_purchase
