from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile, Product, CartItem, Order, OrderItem


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'


class CustomUserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)


try:
    admin.site.unregister(User)
    admin.site.register(User, CustomUserAdmin)
except Exception:
    pass


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'location', 'phone_number', 'is_verified')
    list_filter = ('role', 'is_verified', 'location')
    search_fields = ('user__username', 'phone_number', 'location')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'farmer', 'category', 'price_per_kg', 'stock_quantity', 'unit', 'harvest_date')
    list_filter = ('category', 'unit', 'harvest_date')
    search_fields = ('name', 'farmer__username', 'description')


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('farmer', 'product', 'product_name', 'quantity', 'unit', 'price_per_kg', 'subtotal')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'customer', 'total_amount', 'payment_method', 'payment_status', 'order_status', 'created_at')
    list_filter = ('order_status', 'payment_method', 'payment_status')
    search_fields = ('order_number', 'customer__username', 'contact_phone')
    inlines = [OrderItemInline]


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('customer', 'product', 'quantity', 'created_at')
