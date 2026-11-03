from django.urls import path
from . import views

urlpatterns = [
    # Catalog & Product Details
    path('', views.product_list, name='product_list'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),

    # Cart & Buy Now
    path('cart/', views.cart_view, name='cart_view'),
    path('cart/add/<int:product_id>/', views.cart_add, name='cart_add'),
    path('buy-now/<int:product_id>/', views.buy_now, name='buy_now'),
    path('cart/decrease/<int:product_id>/', views.cart_decrease, name='cart_decrease'),
    path('cart/remove/<int:product_id>/', views.cart_remove, name='cart_remove'),
    path('cart/clear/', views.cart_clear, name='cart_clear'),
    path('cart/api/data/', views.cart_api_data, name='cart_api_data'),

    # Authentication
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Checkout & Orders
    path('checkout/', views.checkout_view, name='checkout'),
    path('order/confirmation/<int:order_id>/', views.order_confirmation, name='order_confirmation'),
    path('orders/', views.my_orders, name='my_orders'),
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),

    # Store Admin Dashboard
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-dashboard/product/add/', views.admin_product_create, name='admin_product_create'),
    path('admin-dashboard/product/<int:pk>/edit/', views.admin_product_edit, name='admin_product_edit'),
    path('admin-dashboard/product/<int:pk>/delete/', views.admin_product_delete, name='admin_product_delete'),
]
