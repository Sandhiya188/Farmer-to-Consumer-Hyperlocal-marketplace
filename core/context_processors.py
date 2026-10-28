from django.conf import settings
from .models import CartItem, UserProfile


def cart_context(request):
    cart_count = 0
    cart_total = 0
    user_profile = None

    if request.user.is_authenticated:
        try:
            user_profile = request.user.profile
        except (UserProfile.DoesNotExist, AttributeError):
            user_profile, _ = UserProfile.objects.get_or_create(
                user=request.user,
                defaults={
                    'role': 'farmer' if (request.user.is_staff or request.user.is_superuser) else 'customer',
                    'location': 'Tamil Nadu',
                    'is_verified': True if request.user.is_superuser else False,
                }
            )

        if (user_profile and user_profile.role == 'customer') or request.user.is_superuser:
            items = CartItem.objects.filter(customer=request.user)
            cart_count = items.count()
            cart_total = sum(item.subtotal for item in items)

    return {
        'global_cart_count': cart_count,
        'global_cart_total': cart_total,
        'current_profile': user_profile,
        'RAZORPAY_KEY_ID': getattr(settings, 'RAZORPAY_KEY_ID', 'rzp_test_SampleKey123'),
        'RAZORPAY_MOCK_MODE': getattr(settings, 'RAZORPAY_MOCK_MODE', True),
    }
