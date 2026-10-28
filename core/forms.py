from django import forms
from django.contrib.auth.models import User
from .models import UserProfile, Product, Order


class UserRegistrationForm(forms.ModelForm):
    ROLE_CHOICES = [
        ('farmer', 'Farmer (Sell Fresh Harvest)'),
        ('customer', 'Customer (Buy Directly from Local Farmers)'),
    ]

    farm_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Farm / Estate Name (For Farmers)'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Create strong password'}),
        min_length=6
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Repeat your password'})
    )
    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'role-radio-input'})
    )
    phone_number = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Mobile Phone Number'})
    )

    location = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'City / Village (e.g. Nashik, Pune)'})
    )
    address = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-input', 'rows': 2, 'placeholder': 'Farm landmark / Home address'})
    )

    class Meta:
        model = User
        fields = ['username', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Choose username'}),
            'email': forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'your.email@example.com'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match!")
        return cleaned_data


class OTPVerificationForm(forms.Form):
    otp = forms.CharField(
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'class': 'form-input otp-input',
            'placeholder': 'Enter 6-digit OTP',
            'autocomplete': 'one-time-code',
            'maxlength': '6',
            'style': 'letter-spacing: 0.35rem; font-size: 1.5rem; text-align: center;'
        })
    )


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'category', 'price_per_kg', 'stock_quantity', 'unit', 'harvest_date', 'description', 'image']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Fresh Red Onions, Alphonso Mangoes'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'price_per_kg': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.50', 'placeholder': 'e.g. 40.00'}),
            'stock_quantity': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.50', 'placeholder': 'e.g. 250'}),
            'unit': forms.Select(attrs={'class': 'form-select'}),
            'harvest_date': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': 'Organic farm grown, picked today morning...'}),
            'image': forms.FileInput(attrs={'class': 'form-input-file'}),
        }


class CheckoutForm(forms.ModelForm):
    PAYMENT_CHOICES = [
        ('cod', 'Cash on Delivery (COD) / Pay on Spot'),
        ('upi', 'Instant UPI / QR Code Payment (Google Pay, PhonePe, Paytm, BHIM)'),
    ]

    payment_method = forms.ChoiceField(
        choices=PAYMENT_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'payment-method-radio'}),
        initial='cod'
    )

    class Meta:
        model = Order
        fields = ['delivery_address', 'delivery_location', 'contact_phone', 'payment_method']
        widgets = {
            'delivery_address': forms.Textarea(attrs={'class': 'form-input', 'rows': 2, 'placeholder': 'Complete Delivery Address / House No / Street'}),
            'delivery_location': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'City / Town / Pincode'}),
            'contact_phone': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Contact phone for delivery'}),
        }
