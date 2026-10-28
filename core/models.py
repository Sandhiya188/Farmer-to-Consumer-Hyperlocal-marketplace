from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
import random


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('farmer', 'Farmer'),
        ('customer', 'Customer'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    farm_name = models.CharField(max_length=150, blank=True, help_text="Farm / Estate Name")
    phone_number = models.CharField(max_length=15, blank=True)
    location = models.CharField(max_length=100, help_text="Region / City / Village")
    district = models.CharField(max_length=100, blank=True, default='', help_text="District")
    address = models.TextField(blank=True, help_text="Full address or farm landmark")
    latitude = models.FloatField(default=18.5204, help_text="GPS Latitude for Map Pin")
    longitude = models.FloatField(default=73.8567, help_text="GPS Longitude for Map Pin")
    is_verified = models.BooleanField(default=False)
    otp = models.CharField(max_length=6, blank=True, null=True)
    otp_created_at = models.DateTimeField(null=True, blank=True)
    otp_attempts = models.IntegerField(default=0, help_text="Failed verification attempts")
    otp_resend_count = models.IntegerField(default=0, help_text="Number of resends in current window")
    otp_last_sent_at = models.DateTimeField(null=True, blank=True, help_text="Last OTP dispatch timestamp")

    def can_resend_otp(self):
        """
        Enforces OTP resend rate-limiting and abuse protection:
        - 60-second cooldown between consecutive requests
        - Maximum 3 resends per 15-minute window
        """
        now = timezone.now()
        if self.otp_last_sent_at:
            elapsed = (now - self.otp_last_sent_at).total_seconds()
            if elapsed < 60:
                wait_sec = int(60 - elapsed)
                return False, f"Please wait {wait_sec} seconds before requesting a new OTP."

            # Reset resend count if 15 minutes have passed
            if elapsed > 900:
                self.otp_resend_count = 0
                self.save(update_fields=['otp_resend_count'])

        if self.otp_resend_count >= 3:
            return False, "Maximum resend limit reached (3 resends). Please try again after 15 minutes."

        return True, ""

    def generate_otp(self, is_resend=False):
        """Generates a secure 6-digit OTP code and updates audit timestamps"""
        new_otp = f"{random.randint(100000, 999999)}"
        now = timezone.now()
        self.otp = new_otp
        self.otp_created_at = now
        self.otp_last_sent_at = now
        self.otp_attempts = 0
        if is_resend:
            self.otp_resend_count += 1
        else:
            self.otp_resend_count = 0

        self.save(update_fields=['otp', 'otp_created_at', 'otp_last_sent_at', 'otp_attempts', 'otp_resend_count'])
        return new_otp

    def verify_otp(self, entered_otp):
        """
        Verifies entered OTP against stored hash/code with strict expiry & abuse limits.
        Returns tuple: (is_valid: bool, message: str)
        """
        if not self.otp or not self.otp_created_at:
            return False, "No active OTP found. Please request a new verification code."

        # Abuse protection: max 5 failed attempts
        if self.otp_attempts >= 5:
            return False, "Maximum verification attempts exceeded (5/5). Please request a fresh OTP."

        # Expiry check: 5 minutes
        expiry_time = self.otp_created_at + timezone.timedelta(minutes=5)
        if timezone.now() > expiry_time:
            return False, "OTP has expired (valid for 5 minutes). Please click 'Resend OTP'."

        if str(self.otp).strip() == str(entered_otp).strip():
            self.is_verified = True
            self.otp = None
            self.otp_attempts = 0
            self.otp_resend_count = 0
            self.save(update_fields=['is_verified', 'otp', 'otp_attempts', 'otp_resend_count'])
            return True, "Phone number verified successfully!"

        self.otp_attempts += 1
        self.save(update_fields=['otp_attempts'])
        remaining = 5 - self.otp_attempts
        if remaining <= 0:
            return False, "Maximum verification attempts exceeded. Please request a new OTP."
        return False, f"Incorrect verification code. {remaining} attempt(s) remaining."

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()} - {self.location})"


class Product(models.Model):
    CATEGORY_CHOICES = [
        ('vegetable', 'Vegetable'),
        ('fruit', 'Fruit'),
    ]

    UNIT_CHOICES = [
        ('kg', 'kg'),
        ('bunch', 'bunch'),
        ('dozen', 'dozen'),
        ('box', 'box'),
    ]

    farmer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='vegetable')
    price_per_kg = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price in ₹")
    stock_quantity = models.DecimalField(max_digits=10, decimal_places=2, help_text="Available Stock")
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES, default='kg')
    description = models.TextField(blank=True, help_text="Farming method, freshness, variety")
    harvest_date = models.DateField(default=timezone.now, help_text="Date when harvested")
    image = models.ImageField(upload_to='harvests/', null=True, blank=True)
    image_url = models.URLField(max_length=500, blank=True, default='', help_text="Original high-res photo URL")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.farmer.username} ({self.stock_quantity} {self.unit} left)"

    @property
    def is_in_stock(self):
        return self.stock_quantity > 0

    @property
    def display_image(self):
        if self.image:
            return self.image.url
        if self.image_url:
            return self.image_url
        if self.category == 'vegetable':
            return 'https://images.unsplash.com/photo-1592924357228-91a4daadcfea?w=600&auto=format&fit=crop&q=80'
        return 'https://images.unsplash.com/photo-1553279768-865429fa0078?w=600&auto=format&fit=crop&q=80'


class CartItem(models.Model):
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cart_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1.0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('customer', 'product')

    @property
    def subtotal(self):
        return round(self.quantity * self.product.price_per_kg, 2)

    def __str__(self):
        return f"{self.customer.username}: {self.product.name} ({self.quantity} {self.product.unit})"


class Order(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('cod', 'Cash on Delivery (COD) / Pay on Spot'),
        ('upi', 'Instant UPI / QR Code Payment (Google Pay, PhonePe, Paytm, BHIM)'),
        ('online_razorpay', 'Instant UPI / Online Payment'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed / Paid'),
        ('failed', 'Failed'),
    ]

    ORDER_STATUS_CHOICES = [
        ('placed', 'Order Confirmed (Placed)'),
        ('preparing', 'Farmer Prepares Order'),
        ('ready', 'Ready for Collection / Delivery'),
        ('delivered', 'Customer Received (Completed)'),
        ('cancelled', 'Cancelled'),
    ]

    order_number = models.CharField(max_length=32, unique=True)
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    delivery_address = models.TextField()
    delivery_location = models.CharField(max_length=100)
    contact_phone = models.CharField(max_length=15)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='cod')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    order_status = models.CharField(max_length=30, choices=ORDER_STATUS_CHOICES, default='placed')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.order_number} by {self.customer.username} (₹{self.total_amount})"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    farmer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='farmer_orders')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    product_name = models.CharField(max_length=100)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=10, default='kg')
    price_per_kg = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product_name} x {self.quantity} for Order #{self.order.order_number}"


@receiver(post_save, sender=User)
def ensure_user_profile(sender, instance, created, **kwargs):
    """Automatically ensure a UserProfile exists whenever a User is created (e.g. createsuperuser)"""
    if created:
        UserProfile.objects.get_or_create(
            user=instance,
            defaults={
                'role': 'farmer' if (instance.is_staff or instance.is_superuser) else 'customer',
                'location': 'Tamil Nadu',
                'district': 'Tamil Nadu',
                'is_verified': True if instance.is_superuser else False,
            }
        )
