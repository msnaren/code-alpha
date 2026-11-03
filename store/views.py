from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Sum
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import transaction

from .models import Category, Product, Order, OrderItem, UserProfile
from .forms import UserRegistrationForm, UserLoginForm, CheckoutForm, ProductForm
from .cart import Cart


def is_staff_user(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)


# ==============================================================================
# CATALOG & PRODUCT VIEWS
# ==============================================================================

def product_list(request):
    """
    ShopKart India Homepage & Product Catalog.
    Supports search by keyword, category filtering, sorting, and pagination.
    """
    products = Product.objects.select_related('category').all()

    # Search filter
    search_query = request.GET.get('q', '').strip()
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(category__name__icontains=search_query)
        )

    # Category filter
    selected_category_slug = request.GET.get('category', '').strip()
    selected_category = None
    if selected_category_slug and selected_category_slug != 'all':
        selected_category = Category.objects.filter(
            Q(slug=selected_category_slug) | Q(name__iexact=selected_category_slug)
        ).first()
        if selected_category:
            products = products.filter(category=selected_category)

    # In-stock only filter
    in_stock_only = request.GET.get('in_stock', '') == '1'
    if in_stock_only:
        products = products.filter(stock__gt=0)

    # Sorting
    sort = request.GET.get('sort', 'featured')
    if sort == 'price_asc':
        products = products.order_by('selling_price')
    elif sort == 'price_desc':
        products = products.order_by('-selling_price')
    elif sort == 'rating_desc':
        products = products.order_by('-rating')
    elif sort == 'name_asc':
        products = products.order_by('name')
    elif sort == 'newest':
        products = products.order_by('-created_at')
    else:  # 'featured' default
        products = products.order_by('-is_featured', '-rating', '-created_at')

    # Pagination: 8 products per page
    total_count = products.count()
    paginator = Paginator(products, 8)
    page_number = request.GET.get('page', 1)

    try:
        page_obj = paginator.get_page(page_number)
    except (PageNotAnInteger, EmptyPage):
        page_obj = paginator.get_page(1)

    categories = Category.objects.all().order_by('name')

    context = {
        'page_obj': page_obj,
        'products': page_obj.object_list,
        'search_query': search_query,
        'selected_category': selected_category,
        'selected_category_slug': selected_category_slug,
        'sort': sort,
        'in_stock_only': in_stock_only,
        'total_count': total_count,
        'categories': categories,
    }
    return render(request, 'store/product_list.html', context)


def product_detail(request, pk):
    """
    Product details page with large image, MRP, discount %, rating,
    stock indicator, quantity selector, related items, and Buy Now action.
    """
    product = get_object_or_404(Product.objects.select_related('category'), pk=pk)
    related_products = Product.objects.filter(
        category=product.category
    ).exclude(id=product.id)[:4]

    context = {
        'product': product,
        'related_products': related_products,
    }
    return render(request, 'store/product_detail.html', context)


# ==============================================================================
# SHOPPING CART & BUY NOW VIEWS
# ==============================================================================

def cart_view(request):
    """
    Shopping cart review page.
    Displays items, quantity controls, delivery charge status, and price breakdown.
    """
    cart = Cart(request)
    return render(request, 'store/cart.html', {'cart': cart})


@require_POST
def cart_add(request, product_id):
    """
    Add a product to cart or increase quantity.
    Supports both traditional POST redirection and asynchronous AJAX requests.
    """
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)

    try:
        quantity = int(request.POST.get('quantity', 1))
    except (ValueError, TypeError):
        quantity = 1

    override = request.POST.get('override', 'false').lower() == 'true'

    if product.stock <= 0:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('format') == 'json':
            return JsonResponse({'success': False, 'message': 'This item is currently out of stock.'}, status=400)
        messages.error(request, f"Sorry, '{product.name}' is currently out of stock.")
        return redirect(request.META.get('HTTP_REFERER', 'product_list'))

    success, msg = cart.add(product, quantity=quantity, override_quantity=override)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('format') == 'json':
        return JsonResponse({
            'success': success,
            'message': msg,
            'cart': cart.get_cart_data()
        })

    if success:
        messages.success(request, f"'{product.name}' was added to your cart.")
    else:
        messages.warning(request, msg)

    return redirect(request.META.get('HTTP_REFERER', 'cart_view'))


@require_POST
def buy_now(request, product_id):
    """
    'Buy Now' fast-track: adds item to cart and immediately redirects to checkout.
    """
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)

    try:
        quantity = int(request.POST.get('quantity', 1))
    except (ValueError, TypeError):
        quantity = 1

    if product.stock <= 0:
        messages.error(request, f"Sorry, '{product.name}' is currently out of stock.")
        return redirect('product_detail', pk=product.id)

    cart.add(product, quantity=quantity, override_quantity=False)
    return redirect('checkout')


@require_POST
def cart_decrease(request, product_id):
    """
    Decrease quantity of a product in the cart.
    """
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.decrease(product)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('format') == 'json':
        return JsonResponse({'success': True, 'cart': cart.get_cart_data()})

    return redirect('cart_view')


@require_POST
def cart_remove(request, product_id):
    """
    Remove an item completely from the cart.
    """
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('format') == 'json':
        return JsonResponse({'success': True, 'cart': cart.get_cart_data()})

    messages.info(request, f"'{product.name}' removed from your cart.")
    return redirect('cart_view')


@require_POST
def cart_clear(request):
    """
    Empty all items in the shopping cart.
    """
    cart = Cart(request)
    cart.clear()
    messages.info(request, "Your cart has been cleared.")
    return redirect('cart_view')


def cart_api_data(request):
    """
    JSON endpoint providing live cart information for frontend syncing.
    """
    cart = Cart(request)
    return JsonResponse(cart.get_cart_data())


# ==============================================================================
# AUTHENTICATION VIEWS
# ==============================================================================

def register_view(request):
    """
    Customer registration collecting Name, Email, 10-digit Indian Mobile, and Password.
    """
    if request.user.is_authenticated:
        return redirect('product_list')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome to ShopKart India, {user.first_name}!")
            next_url = request.POST.get('next') or 'product_list'
            return redirect(next_url)
        else:
            messages.error(request, "Please correct the highlighted errors below.")
    else:
        form = UserRegistrationForm()

    return render(request, 'auth/register.html', {
        'form': form,
        'next': request.GET.get('next', '')
    })


def login_view(request):
    """
    Customer login accepting Email, Username, or 10-digit Mobile Number.
    """
    if request.user.is_authenticated:
        return redirect('product_list')

    next_url = request.GET.get('next', '') or request.POST.get('next', '')

    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            identifier = form.cleaned_data['identifier'].strip()
            password = form.cleaned_data['password']

            user = None
            if '@' in identifier:
                try:
                    user_obj = User.objects.get(email__iexact=identifier)
                    user = authenticate(request, username=user_obj.username, password=password)
                except User.DoesNotExist:
                    user = None
            elif identifier.isdigit() and len(identifier) == 10:
                profile = UserProfile.objects.filter(mobile=identifier).select_related('user').first()
                if profile:
                    user = authenticate(request, username=profile.user.username, password=password)
            else:
                user = authenticate(request, username=identifier, password=password)

            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {user.first_name or user.username}!")
                return redirect(next_url if next_url else 'product_list')
            else:
                messages.error(request, "Invalid login credentials. Please check your username/email and password.")
    else:
        form = UserLoginForm()

    return render(request, 'auth/login.html', {
        'form': form,
        'next': next_url
    })


def logout_view(request):
    """
    Sign out user and redirect to homepage.
    """
    logout(request)
    messages.info(request, "You have been signed out successfully.")
    return redirect('product_list')


# ==============================================================================
# CHECKOUT & ORDER PROCESSING
# ==============================================================================

@login_required(login_url='login')
def checkout_view(request):
    """
    Checkout view: validates inventory, captures Indian delivery address,
    creates Order with SK-2026-XXXX format, decrements stock, and clears cart.
    """
    cart = Cart(request)

    if len(cart) == 0:
        messages.warning(request, "Your cart is empty. Please add products before proceeding to checkout.")
        return redirect('product_list')

    # Pre-checkout stock check
    stock_errors = []
    for item in cart:
        product = item['product']
        if product.stock < item['quantity']:
            if product.stock == 0:
                stock_errors.append(f"'{product.name}' is now out of stock.")
            else:
                stock_errors.append(
                    f"Only {product.stock} units of '{product.name}' remain in stock (you requested {item['quantity']})."
                )

    if stock_errors:
        for err in stock_errors:
            messages.error(request, err)
        return redirect('cart_view')

    profile = getattr(request.user, 'profile', None)

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Re-verify stock inside atomic transaction
                    for item in cart:
                        p = Product.objects.select_for_update().get(id=item['product'].id)
                        if p.stock < item['quantity']:
                            raise ValueError(f"Insufficient stock for '{p.name}'. Available: {p.stock}")

                    # Create order
                    order = form.save(commit=False)
                    order.user = request.user
                    order.subtotal = cart.subtotal
                    order.delivery_charge = cart.delivery_charge
                    order.gst_amount = cart.gst_amount
                    order.total_amount = cart.total_amount
                    order.status = 'Placed'
                    order.save()

                    # Create OrderItem records and decrement stock
                    for item in cart:
                        p = Product.objects.get(id=item['product'].id)
                        OrderItem.objects.create(
                            order=order,
                            product=p,
                            product_name=p.name,
                            price_at_purchase=p.selling_price,
                            quantity=item['quantity']
                        )
                        p.stock -= item['quantity']
                        p.save()

                    # Save shipping details to profile for future convenience
                    if profile:
                        profile.mobile = form.cleaned_data['mobile']
                        profile.address = form.cleaned_data['address']
                        profile.city = form.cleaned_data['city']
                        profile.state = form.cleaned_data['state']
                        profile.pin_code = form.cleaned_data['pin_code']
                        profile.save()

                    # Clear cart after order creation
                    cart.clear()

                    messages.success(request, f"Order #{order.order_number} placed successfully!")
                    return redirect('order_confirmation', order_id=order.id)

            except ValueError as ve:
                messages.error(request, str(ve))
                return redirect('cart_view')
            except Exception as e:
                messages.error(request, "An unexpected error occurred while placing your order. Please try again.")
                return redirect('cart_view')
    else:
        # Prepopulate customer info from user and profile
        initial_data = {
            'full_name': request.user.get_full_name() or request.user.first_name or request.user.username,
            'mobile': profile.mobile if profile else '',
            'address': profile.address if profile else '',
            'city': profile.city if profile else '',
            'state': profile.state if profile else '',
            'pin_code': profile.pin_code if profile else '',
            'payment_method': 'Cash on Delivery',
        }
        form = CheckoutForm(initial=initial_data)

    context = {
        'form': form,
        'cart': cart,
    }
    return render(request, 'store/checkout.html', context)


@login_required(login_url='login')
def order_confirmation(request, order_id):
    """
    Receipt page displaying Order ID, delivery timeline, and order summary.
    """
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'store/order_confirmation.html', {'order': order})


@login_required(login_url='login')
def my_orders(request):
    """
    Customer order history view.
    """
    orders = Order.objects.filter(user=request.user).prefetch_related('items__product').order_by('-created_at')
    return render(request, 'store/my_orders.html', {'orders': orders})


@login_required(login_url='login')
def order_detail(request, order_id):
    """
    Individual past order detailed view.
    """
    if request.user.is_staff:
        order = get_object_or_404(Order, id=order_id)
    else:
        order = get_object_or_404(Order, id=order_id, user=request.user)

    return render(request, 'store/order_detail.html', {'order': order})


# ==============================================================================
# STORE ADMIN DASHBOARD & CRUD
# ==============================================================================

@user_passes_test(is_staff_user, login_url='login')
def admin_dashboard(request):
    """
    Store owner administration dashboard with metrics in ₹, low stock alerts,
    and product management.
    """
    total_products = Product.objects.count()
    total_orders = Order.objects.count()
    total_users = User.objects.count()
    total_revenue = Order.objects.exclude(
        status='Cancelled'
    ).aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')

    low_stock_products = Product.objects.filter(stock__lte=5)
    recent_orders = Order.objects.select_related('user').order_by('-created_at')[:10]
    all_products = Product.objects.select_related('category').order_by('-created_at')

    context = {
        'total_products': total_products,
        'total_orders': total_orders,
        'total_users': total_users,
        'total_revenue': total_revenue,
        'low_stock_products': low_stock_products,
        'recent_orders': recent_orders,
        'all_products': all_products,
    }
    return render(request, 'store/admin_dashboard.html', context)


@user_passes_test(is_staff_user, login_url='login')
def admin_product_create(request):
    """
    Add new product through the Store Admin portal.
    """
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save()
            messages.success(request, f"Product '{product.name}' created successfully!")
            return redirect('admin_dashboard')
    else:
        form = ProductForm()

    return render(request, 'store/admin_product_form.html', {
        'form': form,
        'title': 'Add New Indian Product',
        'is_new': True
    })


@user_passes_test(is_staff_user, login_url='login')
def admin_product_edit(request, pk):
    """
    Edit an existing product.
    """
    product = get_object_or_404(Product, pk=pk)

    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, f"Product '{product.name}' updated successfully!")
            return redirect('admin_dashboard')
    else:
        form = ProductForm(instance=product)

    return render(request, 'store/admin_product_form.html', {
        'form': form,
        'product': product,
        'title': f'Edit Product: {product.name}',
        'is_new': False
    })


@user_passes_test(is_staff_user, login_url='login')
@require_POST
def admin_product_delete(request, pk):
    """
    Delete a product from catalog.
    """
    product = get_object_or_404(Product, pk=pk)
    name = product.name
    try:
        product.delete()
        messages.success(request, f"Product '{name}' was deleted.")
    except Exception:
        messages.error(request, f"Could not delete '{name}' because it has linked order records.")
    return redirect('admin_dashboard')
