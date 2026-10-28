from django.urls import path
from . import views

urlpatterns = [
    # Home & Auth
    path('', views.home_view, name='home'),
    path('register/', views.register_view, name='register'),
    path('verify-otp/', views.verify_otp_view, name='verify_otp'),
    path('resend-otp/', views.resend_otp_view, name='resend_otp'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Farmer Workflow
    path('farmer/dashboard/', views.farmer_dashboard, name='farmer_dashboard'),
    path('farmer/products/add/', views.add_product_view, name='add_product'),
    path('farmer/products/<int:product_id>/edit/', views.edit_product_view, name='edit_product'),
    path('farmer/products/<int:product_id>/delete/', views.delete_product_view, name='delete_product'),
    path('farmer/orders/', views.farmer_orders_view, name='farmer_orders'),
    path('farmer/orders/<int:order_id>/update-status/', views.update_order_status_view, name='update_order_status'),

    # Customer Workflow
    path('browse/', views.customer_browse_view, name='customer_browse'),
    path('products/<int:product_id>/', views.product_detail_view, name='product_detail'),
    path('cart/', views.cart_view, name='cart_view'),
    path('cart/add/<int:product_id>/', views.add_to_cart_view, name='add_to_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart_view, name='remove_from_cart'),
    path('cart/update-ajax/', views.update_cart_ajax, name='update_cart_ajax'),
    path('checkout/', views.checkout_view, name='checkout'),
    
    # Payments & Confirmation (UPI Payment)
    path('payment/upi/<int:order_id>/', views.upi_payment_view, name='upi_payment'),
    path('payment/upi/<int:order_id>/verify/', views.upi_verify_view, name='upi_verify'),
    path('payment/razorpay/<int:order_id>/', views.upi_payment_view, name='razorpay_payment'),
    path('payment/razorpay/<int:order_id>/verify/', views.upi_verify_view, name='razorpay_verify'),
    path('orders/<int:order_id>/success/', views.order_success_view, name='order_success'),
    path('orders/', views.customer_orders_view, name='customer_orders'),
    path('orders/<int:order_id>/', views.order_detail_view, name='order_detail'),
]
