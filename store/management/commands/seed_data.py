from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from store.models import Category, Product, UserProfile, Order, OrderItem

CATEGORIES_DATA = [
    {"name": "Electronics", "slug": "electronics"},
    {"name": "Fashion", "slug": "fashion"},
    {"name": "Home & Kitchen", "slug": "home-kitchen"},
    {"name": "Beauty", "slug": "beauty"},
    {"name": "Books", "slug": "books"},
    {"name": "Grocery", "slug": "grocery"},
]

PRODUCTS_DATA = [
    # Electronics
    {
        "name": "Apex Wireless Bluetooth Earbuds (Active Noise Cancellation)",
        "category_slug": "electronics",
        "mrp": Decimal("2999.00"),
        "selling_price": Decimal("1299.00"),
        "stock": 35,
        "rating": Decimal("4.6"),
        "is_featured": True,
        "image": "https://images.unsplash.com/photo-1590658268037-6bf12165a8df?auto=format&fit=crop&w=600&q=80",
        "description": "True Wireless Stereo (TWS) earbuds engineered with 10mm dynamic bass drivers, 42 hours combined battery backup with fast charging case, IPX5 sweat resistance, and quad ENC microphones for crystal-clear calling."
    },
    {
        "name": "UltraSlim 20000mAh Fast Charging Power Bank",
        "category_slug": "electronics",
        "mrp": Decimal("2499.00"),
        "selling_price": Decimal("1199.00"),
        "stock": 20,
        "rating": Decimal("4.5"),
        "is_featured": True,
        "image": "https://images.unsplash.com/photo-1609592426867-0c2b7fc06734?auto=format&fit=crop&w=600&q=80",
        "description": "High-capacity 20,000mAh lithium-polymer power bank with 22.5W two-way fast charging. Features dual USB-A output, Type-C Power Delivery (PD) port, and 12-layer advanced circuit protection."
    },

    # Fashion
    {
        "name": "Men's Pure Cotton Handloom Kurta (Mustard Yellow)",
        "category_slug": "fashion",
        "mrp": Decimal("1899.00"),
        "selling_price": Decimal("899.00"),
        "stock": 28,
        "rating": Decimal("4.4"),
        "is_featured": True,
        "image": "https://images.unsplash.com/photo-1597983073493-88cd35cf93b0?auto=format&fit=crop&w=600&q=80",
        "description": "Elegantly tailored traditional Indian men's long kurta crafted from 100% breathable organic handspun cotton. Styled with a mandarin collar, wooden buttons, and two deep side pockets."
    },
    {
        "name": "Women's Traditional Kanjivaram Silk Saree (Peacock Blue)",
        "category_slug": "fashion",
        "mrp": Decimal("4999.00"),
        "selling_price": Decimal("2499.00"),
        "stock": 14,
        "rating": Decimal("4.8"),
        "is_featured": True,
        "image": "https://images.unsplash.com/photo-1610030469983-98e550d6193c?auto=format&fit=crop&w=600&q=80",
        "description": "Luxurious South Indian Kanjivaram art silk saree adorned with intricate golden zari floral motifs, grand pallu border, and matching unstitched blouse piece. Ideal for weddings and festive pujas."
    },

    # Home & Kitchen
    {
        "name": "Stainless Steel Insulated Water Bottle (1 Litre)",
        "category_slug": "home-kitchen",
        "mrp": Decimal("899.00"),
        "selling_price": Decimal("449.00"),
        "stock": 45,
        "rating": Decimal("4.7"),
        "is_featured": True,
        "image": "https://images.unsplash.com/photo-1602143407151-7111542de6e8?auto=format&fit=crop&w=600&q=80",
        "description": "Double-wall vacuum insulated 304 food-grade stainless steel bottle. Keeps water cold for up to 24 hours and hot for up to 12 hours. Rust-free, BPA-free, leak-proof screw cap with silicon carry loop."
    },
    {
        "name": "Cast Iron Pre-Seasoned Dosa Tawa (28cm)",
        "category_slug": "home-kitchen",
        "mrp": Decimal("1699.00"),
        "selling_price": Decimal("899.00"),
        "stock": 18,
        "rating": Decimal("4.6"),
        "is_featured": False,
        "image": "https://images.unsplash.com/photo-1590794056226-79ef3a8147e1?auto=format&fit=crop&w=600&q=80",
        "description": "Heavy-duty authentic cast iron flat tawa pre-seasoned with 100% natural vegetable oil. Ensures even heat distribution for crispy golden dosas, rotis, parathas, and chapatis. Enriches food with natural dietary iron."
    },
    {
        "name": "Artisan Pure Copper Water Dispenser Pot (5 Litre)",
        "category_slug": "home-kitchen",
        "mrp": Decimal("2499.00"),
        "selling_price": Decimal("1499.00"),
        "stock": 4,  # Low stock test case
        "rating": Decimal("4.8"),
        "is_featured": False,
        "image": "https://images.unsplash.com/photo-1584285418504-0051b3d37704?auto=format&fit=crop&w=600&q=80",
        "description": "Handcrafted 100% pure Ayurvedic copper matka dispenser with brass chrome faucet tap. Storing drinking water overnight in copper vessels provides documented holistic digestive and antioxidant benefits."
    },

    # Beauty
    {
        "name": "Pure Ayurvedic Kumkumadi Radiance Face Cream (50g)",
        "category_slug": "beauty",
        "mrp": Decimal("699.00"),
        "selling_price": Decimal("349.00"),
        "stock": 30,
        "rating": Decimal("4.5"),
        "is_featured": True,
        "image": "https://images.unsplash.com/photo-1556228720-195a672e8a03?auto=format&fit=crop&w=600&q=80",
        "description": "Infused with authentic Kashmiri saffron, sandalwood, and 16 precious Ayurvedic herbs. Deeply nourishes the skin, reduces dark spots, enhances natural glow, and contains zero parabens or artificial fragrances."
    },
    {
        "name": "Herbal Bhringraj & Amla Hair Growth Oil (200ml)",
        "category_slug": "beauty",
        "mrp": Decimal("499.00"),
        "selling_price": Decimal("299.00"),
        "stock": 25,
        "rating": Decimal("4.7"),
        "is_featured": False,
        "image": "https://images.unsplash.com/photo-1608248597359-bb436d4bc225?auto=format&fit=crop&w=600&q=80",
        "description": "Traditional Ayurvedic hair therapy prepared with cold-pressed sesame oil, fresh Bhringraj leaves, Amla, and Brahmi. Strengthens hair roots from within, prevents premature graying, and promotes dense hair growth."
    },

    # Books
    {
        "name": "Mastering Python Programming (Indian Edition)",
        "category_slug": "books",
        "mrp": Decimal("999.00"),
        "selling_price": Decimal("599.00"),
        "stock": 50,
        "rating": Decimal("4.9"),
        "is_featured": True,
        "image": "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?auto=format&fit=crop&w=600&q=80",
        "description": "Comprehensive textbook covering modern Python 3.11+, Django full-stack web development, object-oriented design, REST APIs, and database engineering. Features real-world project tutorials and interview questions."
    },
    {
        "name": "Wings of Fire by Dr. A.P.J. Abdul Kalam",
        "category_slug": "books",
        "mrp": Decimal("399.00"),
        "selling_price": Decimal("249.00"),
        "stock": 40,
        "rating": Decimal("4.9"),
        "is_featured": False,
        "image": "https://images.unsplash.com/photo-1512820790803-83ca734da794?auto=format&fit=crop&w=600&q=80",
        "description": "The inspiring autobiography of Dr. A.P.J. Abdul Kalam, former President of India and renowned aerospace scientist. Chronicles his journey from humble beginnings in Rameswaram to leading India's space program."
    },

    # Grocery
    {
        "name": "Royal Daawat Traditional Basmati Rice (5kg Bag)",
        "category_slug": "grocery",
        "mrp": Decimal("899.00"),
        "selling_price": Decimal("649.00"),
        "stock": 22,
        "rating": Decimal("4.8"),
        "is_featured": True,
        "image": "https://images.unsplash.com/photo-1586201375761-83865001e31c?auto=format&fit=crop&w=600&q=80",
        "description": "Aged for 2 years in Himalayan climate. Extra-long pearl white grains that elongate up to 2.5 times upon cooking with a divine sweet aroma. Perfect for authentic Royal Hyderabadi Biryani and Pulao."
    },
    {
        "name": "Tata Tea Gold Premium Black Tea Blend (1kg)",
        "category_slug": "grocery",
        "mrp": Decimal("620.00"),
        "selling_price": Decimal("479.00"),
        "stock": 35,
        "rating": Decimal("4.7"),
        "is_featured": False,
        "image": "https://images.unsplash.com/photo-1576092768241-dec231879fc3?auto=format&fit=crop&w=600&q=80",
        "description": "Exquisite blend of fine Assam CTC tea leaves gently combined with 15% gently rolled long aromatic leaves. Delivers rich golden liquor, invigorating aroma, and irresistible brisk taste with every cup of chai."
    },
    {
        "name": "Organic Cold-Pressed Kachi Ghani Mustard Oil (1 Litre)",
        "category_slug": "grocery",
        "mrp": Decimal("320.00"),
        "selling_price": Decimal("219.00"),
        "stock": 28,
        "rating": Decimal("4.6"),
        "is_featured": False,
        "image": "https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?auto=format&fit=crop&w=600&q=80",
        "description": "Extracted traditionally from premium Rajasthan brown mustard seeds using slow wooden kolhu presses at room temperature. Retains all natural pungency, essential fatty acids, and high omega-3 content."
    },
    {
        "name": "Pure Kashmiri Mongra Saffron / Kesar (1g Grade A1)",
        "category_slug": "grocery",
        "mrp": Decimal("499.00"),
        "selling_price": Decimal("399.00"),
        "stock": 0,  # Out of stock test case
        "rating": Decimal("4.8"),
        "is_featured": False,
        "image": "https://images.unsplash.com/photo-1615485290382-441e4d049cb5?auto=format&fit=crop&w=600&q=80",
        "description": "Hand-plucked crimson stigmas harvested directly from the saffron valley of Pampore, Kashmir. Rich in crocin and safranal giving deep natural red tint and intoxicating aroma to sweets, biryani, and milk."
    }
]


class Command(BaseCommand):
    help = "Seed database with Indian categories, realistic products in INR, superuser, and demo customer."

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.NOTICE("Initializing ShopKart India Database Seeding..."))

        # 1. Categories
        cat_map = {}
        for cdata in CATEGORIES_DATA:
            cat, created = Category.objects.get_or_create(
                slug=cdata["slug"],
                defaults={"name": cdata["name"]}
            )
            cat_map[cdata["slug"]] = cat
        self.stdout.write(self.style.SUCCESS(f"Seeded {len(cat_map)} categories."))

        # 2. Superuser (admin / Admin@123)
        admin_user, a_created = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@shopkart.in",
                "first_name": "ShopKart Admin",
                "is_staff": True,
                "is_superuser": True
            }
        )
        admin_user.set_password("Admin@123")
        admin_user.email = "admin@shopkart.in"
        admin_user.first_name = "ShopKart Admin"
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.save()

        UserProfile.objects.get_or_create(
            user=admin_user,
            defaults={
                "mobile": "9876500001",
                "address": "ShopKart HQ, Indiranagar",
                "city": "Bengaluru",
                "state": "Karnataka",
                "pin_code": "560038"
            }
        )
        self.stdout.write(self.style.SUCCESS("Superuser configured: admin / Admin@123 (admin@shopkart.in)"))

        # 3. Demo Customer (rahul / Password@123)
        demo_user, d_created = User.objects.get_or_create(
            username="rahul",
            defaults={
                "email": "rahul.sharma@example.com",
                "first_name": "Rahul Sharma",
            }
        )
        demo_user.set_password("Password@123")
        demo_user.email = "rahul.sharma@example.com"
        demo_user.first_name = "Rahul Sharma"
        demo_user.save()

        UserProfile.objects.update_or_create(
            user=demo_user,
            defaults={
                "mobile": "9876543210",
                "address": "Flat 402, Shanti Vihar, MG Road",
                "city": "Bengaluru",
                "state": "Karnataka",
                "pin_code": "560001"
            }
        )
        self.stdout.write(self.style.SUCCESS("Demo customer configured: rahul / Password@123 (rahul.sharma@example.com)"))

        # 4. Products
        p_count = 0
        for pdata in PRODUCTS_DATA:
            category = cat_map[pdata["category_slug"]]
            Product.objects.update_or_create(
                name=pdata["name"],
                defaults={
                    "category": category,
                    "mrp": pdata["mrp"],
                    "selling_price": pdata["selling_price"],
                    "stock": pdata["stock"],
                    "rating": pdata["rating"],
                    "is_featured": pdata["is_featured"],
                    "image": pdata["image"],
                    "description": pdata["description"],
                }
            )
            p_count += 1
        self.stdout.write(self.style.SUCCESS(f"Seeded {p_count} Indian products with realistic INR pricing."))

        # 5. Create an initial sample completed order for demo user
        if not Order.objects.filter(user=demo_user).exists():
            sample_product = Product.objects.filter(selling_price__gte=Decimal('999.00')).first()
            if sample_product:
                subtotal = sample_product.selling_price
                delivery = Decimal('0.00') if subtotal >= 999 else Decimal('49.00')
                gst = round(subtotal * Decimal('0.18'), 2)
                total = subtotal + delivery

                order = Order.objects.create(
                    user=demo_user,
                    full_name="Rahul Sharma",
                    mobile="9876543210",
                    address="Flat 402, Shanti Vihar, MG Road",
                    city="Bengaluru",
                    state="Karnataka",
                    pin_code="560001",
                    payment_method="UPI",
                    subtotal=subtotal,
                    delivery_charge=delivery,
                    gst_amount=gst,
                    total_amount=total,
                    status="Delivered"
                )
                OrderItem.objects.create(
                    order=order,
                    product=sample_product,
                    product_name=sample_product.name,
                    price_at_purchase=sample_product.selling_price,
                    quantity=1
                )
                self.stdout.write(self.style.SUCCESS(f"Created sample past order #{order.order_number} for demo user."))

        self.stdout.write(self.style.SUCCESS("ShopKart India database seed completed successfully!"))
