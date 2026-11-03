from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Category, Product, Order, OrderItem, UserProfile
from .cart import Cart


class ShopKartIndiaCatalogTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.cat_electronics = Category.objects.create(name="Electronics", slug="electronics")
        self.cat_fashion = Category.objects.create(name="Fashion", slug="fashion")

        self.p1 = Product.objects.create(
            name="Apex Wireless Earbuds",
            category=self.cat_electronics,
            mrp=Decimal("2999.00"),
            selling_price=Decimal("1299.00"),
            stock=15,
            rating=Decimal("4.6"),
            description="True wireless earbuds with heavy bass"
        )
        self.p2 = Product.objects.create(
            name="Cotton Handloom Kurta",
            category=self.cat_fashion,
            mrp=Decimal("1899.00"),
            selling_price=Decimal("899.00"),
            stock=20,
            rating=Decimal("4.4"),
            description="Pure cotton ethnic wear"
        )
        self.p3 = Product.objects.create(
            name="Out of Stock Saffron",
            category=self.cat_electronics,
            mrp=Decimal("499.00"),
            selling_price=Decimal("399.00"),
            stock=0,
            rating=Decimal("4.8"),
            description="Sold out item"
        )

    def test_catalog_homepage(self):
        response = self.client.get(reverse('product_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Apex Wireless Earbuds")
        self.assertContains(response, "Cotton Handloom Kurta")
        # Check Indian Rupee symbol & formatting
        self.assertContains(response, "1,299")
        self.assertContains(response, "899")

    def test_product_search(self):
        response = self.client.get(reverse('product_list'), {'q': 'Kurta'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cotton Handloom Kurta")
        self.assertNotContains(response, "Apex Wireless Earbuds")

    def test_category_filter(self):
        response = self.client.get(reverse('product_list'), {'category': 'electronics'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Apex Wireless Earbuds")
        self.assertNotContains(response, "Cotton Handloom Kurta")

    def test_product_detail(self):
        response = self.client.get(reverse('product_detail', args=[self.p1.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Apex Wireless Earbuds")
        self.assertContains(response, "1,299")
        self.assertContains(response, "2,999")
        self.assertContains(response, "ADD TO CART")
        self.assertContains(response, "BUY NOW")


class ShopKartIndiaCartAndCheckoutTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="rahul",
            email="rahul.sharma@example.com",
            password="Password@123",
            first_name="Rahul Sharma"
        )
        UserProfile.objects.create(
            user=self.user,
            mobile="9876543210",
            address="Flat 402, MG Road",
            city="Bengaluru",
            state="Karnataka",
            pin_code="560001"
        )

        self.category = Category.objects.create(name="Electronics", slug="electronics")
        self.product = Product.objects.create(
            name="Fast Charging Power Bank",
            category=self.category,
            mrp=Decimal("2499.00"),
            selling_price=Decimal("1199.00"),
            stock=10,
            rating=Decimal("4.5"),
            description="20000mAh portable charger"
        )

    def test_cart_operations_and_calculations(self):
        # Add product to cart
        response = self.client.post(reverse('cart_add', args=[self.product.id]), {'quantity': 1})
        self.assertEqual(response.status_code, 302)

        # Check cart view
        response = self.client.get(reverse('cart_view'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Fast Charging Power Bank")
        self.assertContains(response, "1,199")
        # Subtotal is 1199 >= 999, so delivery should be FREE
        self.assertContains(response, "FREE")

    def test_buy_now_redirects_to_checkout(self):
        self.client.login(username="rahul", password="Password@123")
        response = self.client.post(reverse('buy_now', args=[self.product.id]), {'quantity': 1})
        self.assertRedirects(response, reverse('checkout'))

    def test_successful_checkout_creates_order_and_reduces_stock(self):
        self.client.login(username="rahul", password="Password@123")
        self.client.post(reverse('cart_add', args=[self.product.id]), {'quantity': 2})

        checkout_data = {
            'full_name': 'Rahul Sharma',
            'mobile': '9876543210',
            'address': 'Flat 402, MG Road',
            'city': 'Bengaluru',
            'state': 'Karnataka',
            'pin_code': '560001',
            'payment_method': 'Cash on Delivery',
        }
        response = self.client.post(reverse('checkout'), checkout_data)
        self.assertEqual(response.status_code, 302)

        # Check order record
        order = Order.objects.filter(user=self.user).first()
        self.assertIsNotNone(order)
        self.assertTrue(order.order_number.startswith('SK-'))
        self.assertEqual(order.subtotal, Decimal("2398.00"))
        self.assertEqual(order.delivery_charge, Decimal("0.00"))
        self.assertEqual(order.total_amount, Decimal("2398.00"))

        # Check stock reduction
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 8)


class ShopKartIndiaAuthTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_registration_with_indian_mobile(self):
        response = self.client.post(reverse('register'), {
            'name': 'Priya Patel',
            'email': 'priya.patel@example.com',
            'mobile': '9822334455',
            'password': 'SecurePassword@123',
            'confirm_password': 'SecurePassword@123',
        })
        self.assertEqual(response.status_code, 302)
        user = User.objects.filter(email='priya.patel@example.com').first()
        self.assertIsNotNone(user)
        self.assertEqual(user.profile.mobile, '9822334455')

    def test_invalid_mobile_rejected(self):
        response = self.client.post(reverse('register'), {
            'name': 'Invalid Mobile User',
            'email': 'invalid@example.com',
            'mobile': '12345',  # invalid Indian mobile
            'password': 'SecurePassword@123',
            'confirm_password': 'SecurePassword@123',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context['form'], 'mobile', 'Please enter a valid 10-digit Indian mobile number starting with 6, 7, 8, or 9.')
