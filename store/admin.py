from django.contrib import admin
from .models import Category, Product, UserProfile, Cart, CartItem, Order, OrderItem


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'selling_price', 'mrp', 'stock', 'rating', 'is_featured', 'created_at')
    list_filter = ('category', 'is_featured', 'created_at')
    list_editable = ('selling_price', 'stock', 'is_featured')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('-created_at',)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'product_name', 'price_at_purchase', 'quantity', 'subtotal')

    def subtotal(self, instance):
        return f"₹{instance.subtotal:.2f}"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'user', 'full_name', 'mobile', 'total_amount', 'status', 'created_at')
    list_filter = ('status', 'payment_method', 'created_at')
    list_editable = ('status',)
    search_fields = ('order_number', 'full_name', 'mobile', 'user__username', 'pin_code')
    inlines = [OrderItemInline]
    ordering = ('-created_at',)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'mobile', 'city', 'state', 'pin_code')
    search_fields = ('user__username', 'user__email', 'mobile', 'city')


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'product_name', 'price_at_purchase', 'quantity')


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'session_key', 'total_count', 'total_amount', 'created_at')
