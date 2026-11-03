import re
from decimal import Decimal
from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import Product, Order, UserProfile, Category

INDIAN_STATES = [
    ('Andhra Pradesh', 'Andhra Pradesh'),
    ('Arunachal Pradesh', 'Arunachal Pradesh'),
    ('Assam', 'Assam'),
    ('Bihar', 'Bihar'),
    ('Chhattisgarh', 'Chhattisgarh'),
    ('Goa', 'Goa'),
    ('Gujarat', 'Gujarat'),
    ('Haryana', 'Haryana'),
    ('Himachal Pradesh', 'Himachal Pradesh'),
    ('Jharkhand', 'Jharkhand'),
    ('Karnataka', 'Karnataka'),
    ('Kerala', 'Kerala'),
    ('Madhya Pradesh', 'Madhya Pradesh'),
    ('Maharashtra', 'Maharashtra'),
    ('Manipur', 'Manipur'),
    ('Meghalaya', 'Meghalaya'),
    ('Mizoram', 'Mizoram'),
    ('Nagaland', 'Nagaland'),
    ('Odisha', 'Odisha'),
    ('Punjab', 'Punjab'),
    ('Rajasthan', 'Rajasthan'),
    ('Sikkim', 'Sikkim'),
    ('Tamil Nadu', 'Tamil Nadu'),
    ('Telangana', 'Telangana'),
    ('Tripura', 'Tripura'),
    ('Uttar Pradesh', 'Uttar Pradesh'),
    ('Uttarakhand', 'Uttarakhand'),
    ('West Bengal', 'West Bengal'),
    ('Delhi (NCT)', 'Delhi (NCT)'),
    ('Jammu and Kashmir', 'Jammu and Kashmir'),
    ('Ladakh', 'Ladakh'),
    ('Chandigarh', 'Chandigarh'),
    ('Puducherry', 'Puducherry'),
]


class UserRegistrationForm(forms.ModelForm):
    """
    Registration form collecting Full Name, Email, 10-digit Mobile Number,
    and Password with confirmation.
    """
    name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'e.g. Rahul Sharma',
            'autocomplete': 'name',
            'required': True
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'rahul.sharma@example.com',
            'autocomplete': 'email',
            'required': True
        })
    )
    mobile = forms.CharField(
        max_length=10,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': '10-digit mobile number (e.g. 9876543210)',
            'pattern': '[6-9][0-9]{9}',
            'maxlength': '10',
            'required': True
        }),
        help_text="Enter a valid 10-digit Indian mobile number."
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Create strong password (min 6 characters)',
            'autocomplete': 'new-password',
            'required': True
        }),
        min_length=6
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Confirm your password',
            'autocomplete': 'new-password',
            'required': True
        })
    )

    class Meta:
        model = User
        fields = ['name', 'email', 'password']

    def clean_mobile(self):
        mobile = self.cleaned_data.get('mobile', '').strip()
        # Clean non-digits
        mobile = re.sub(r'\D', '', mobile)
        if not re.match(r'^[6-9]\d{9}$', mobile):
            raise ValidationError("Please enter a valid 10-digit Indian mobile number starting with 6, 7, 8, or 9.")
        return mobile

    def clean_email(self):
        email = self.cleaned_data.get('email', '').lower().strip()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("An account with this email address already exists. Please sign in.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match. Please verify and retype.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        name = self.cleaned_data['name'].strip()
        user.first_name = name
        user.email = self.cleaned_data['email'].lower().strip()

        # Derive clean username
        base_username = user.email.split('@')[0]
        username = base_username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        user.username = username
        user.set_password(self.cleaned_data['password'])

        if commit:
            user.save()
            # Create or update user profile with mobile number
            UserProfile.objects.update_or_create(
                user=user,
                defaults={'mobile': self.cleaned_data['mobile']}
            )

        return user


class UserLoginForm(forms.Form):
    """
    User login form accepting Email, Username, or Mobile along with Password.
    """
    identifier = forms.CharField(
        label="Email, Username, or Mobile",
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter your registered Email or Username',
            'autocomplete': 'username',
            'required': True
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter password',
            'autocomplete': 'current-password',
            'required': True
        })
    )


class CheckoutForm(forms.ModelForm):
    """
    Indian e-commerce checkout form capturing delivery address,
    10-digit mobile, 6-digit PIN code, state, and payment method.
    """
    state = forms.ChoiceField(
        choices=[('', '-- Select Indian State / UT --')] + INDIAN_STATES,
        widget=forms.Select(attrs={'class': 'form-select', 'required': True})
    )

    class Meta:
        model = Order
        fields = [
            'full_name',
            'mobile',
            'address',
            'city',
            'state',
            'pin_code',
            'payment_method',
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Recipient Full Name (e.g. Rahul Sharma)',
                'required': True,
            }),
            'mobile': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': '10-digit Mobile Number',
                'maxlength': '10',
                'pattern': '[6-9][0-9]{9}',
                'required': True,
            }),
            'address': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Flat, House No., Building, Street / Locality',
                'required': True,
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'City / Town / District (e.g. Bengaluru, Mumbai)',
                'required': True,
            }),
            'pin_code': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': '6-Digit PIN Code (e.g. 560001)',
                'maxlength': '6',
                'pattern': '[1-9][0-9]{5}',
                'required': True,
            }),
            'payment_method': forms.RadioSelect(attrs={
                'class': 'payment-radio',
            }),
        }

    def clean_mobile(self):
        mobile = self.cleaned_data.get('mobile', '').strip()
        mobile = re.sub(r'\D', '', mobile)
        if not re.match(r'^[6-9]\d{9}$', mobile):
            raise ValidationError("Please provide a valid 10-digit Indian mobile number.")
        return mobile

    def clean_pin_code(self):
        pin = self.cleaned_data.get('pin_code', '').strip()
        if not re.match(r'^[1-9][0-9]{5}$', pin):
            raise ValidationError("Please enter a valid 6-digit Indian Postal PIN Code.")
        return pin


class ProductForm(forms.ModelForm):
    """
    Admin form to create or edit products in ShopKart India.
    """
    class Meta:
        model = Product
        fields = [
            'name',
            'category',
            'mrp',
            'selling_price',
            'stock',
            'rating',
            'is_featured',
            'image',
            'description',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'e.g. Apex Wireless Earbuds',
                'required': True,
            }),
            'category': forms.Select(attrs={
                'class': 'form-select',
                'required': True,
            }),
            'mrp': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': 'Maximum Retail Price (₹)',
                'step': '0.01',
                'min': '1',
                'required': True,
            }),
            'selling_price': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': 'Selling Price in INR (₹)',
                'step': '0.01',
                'min': '1',
                'required': True,
            }),
            'stock': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': 'Available Stock Quantity',
                'min': '0',
                'required': True,
            }),
            'rating': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': 'Customer Rating (e.g. 4.5)',
                'step': '0.1',
                'min': '1.0',
                'max': '5.0',
                'required': True,
            }),
            'image': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'https://images.unsplash.com/... or /static/images/...',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-textarea',
                'placeholder': 'Detailed product description and specifications...',
                'rows': 4,
                'required': True,
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        mrp = cleaned_data.get('mrp')
        selling_price = cleaned_data.get('selling_price')

        if mrp and selling_price and selling_price > mrp:
            self.add_error('selling_price', "Selling price cannot be greater than Maximum Retail Price (MRP).")

        return cleaned_data
