from django import forms
from django.contrib.auth.models import User
from .models import UserProfile, Product, Order


class UserRegistrationForm(forms.ModelForm):
    ROLE_CHOICES = [
        ('farmer', 'Farmer (Sell Fresh Harvest)'),
        ('customer', 'Customer (Buy Directly from Local Farmers)'),
    ]

    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'role-radio-input'})
    )
    full_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Full Name (e.g. Ramesh Kumar)'})
    )
    phone_number = forms.CharField(
        max_length=15,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': '10-digit Mobile Phone Number'})
    )
    district = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'District (e.g. Coimbatore, Madurai, Salem)'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Create strong password'}),
        min_length=6
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Repeat your password'})
    )

    # Farmer-specific details
    farm_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Farm / Estate Name (e.g. Green Valley Farm)'})
    )
    farm_location = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Farm Village / Area (e.g. Pollachi Village)'})
    )
    farm_address = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-input', 'rows': 2, 'placeholder': 'Detailed Farm Landmark / Street Address'})
    )

    # Customer-specific details
    delivery_address = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-input', 'rows': 2, 'placeholder': 'House/Flat No, Street, Landmark for Delivery'})
    )
    city_town = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'City / Town / Area (Optional)'})
    )

    class Meta:
        model = User
        fields = ['username', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Choose unique username'}),
            'email': forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'your.email@example.com'}),
        }

    def clean_phone_number(self):
        raw_phone = self.cleaned_data.get('phone_number', '').strip()
        clean = raw_phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
        if clean.startswith('+91'):
            clean = clean[3:]
        elif clean.startswith('0'):
            clean = clean[1:]
        if not clean.isdigit() or len(clean) != 10:
            raise forms.ValidationError("Please enter a valid 10-digit Indian mobile number.")
        return clean

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match!")

        role = cleaned_data.get('role')
        if role == 'farmer':
            if not cleaned_data.get('farm_name'):
                self.add_error('farm_name', "Farm Name is required for Farmer registration.")
            if not cleaned_data.get('farm_location'):
                self.add_error('farm_location', "Farm Location / Village is required for Farmers.")
            if not cleaned_data.get('district'):
                self.add_error('district', "District is required.")
        elif role == 'customer':
            if not cleaned_data.get('delivery_address'):
                self.add_error('delivery_address', "Delivery Address is required for Customer registration.")
            if not cleaned_data.get('district'):
                self.add_error('district', "District is required.")

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

    def clean_otp(self):
        val = self.cleaned_data.get('otp', '').strip()
        if not val.isdigit() or len(val) != 6:
            raise forms.ValidationError("OTP must be exactly 6 numeric digits.")
        return val


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
