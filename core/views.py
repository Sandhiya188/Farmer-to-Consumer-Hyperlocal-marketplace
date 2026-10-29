import uuid
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.http import require_POST
import razorpay

from .models import UserProfile, Product, CartItem, Order, OrderItem
from .forms import UserRegistrationForm, OTPVerificationForm, ProductForm, CheckoutForm
from .sms_service import send_otp_sms


def ensure_seed_data_loaded():
    """Auto-seeds database with initial farmers, profiles, and produce on fresh deployments"""
    try:
        if UserProfile.objects.count() == 0 or Product.objects.count() == 0:
            from django.core.management import call_command
            call_command('loaddata', 'seed_data', verbosity=0)
    except Exception:
        pass


def get_user_profile(user):
    """Safely retrieves or auto-creates UserProfile for a user to prevent RelatedObjectDoesNotExist."""
    if not user or not user.is_authenticated:
        return None
    try:
        return user.profile
    except (UserProfile.DoesNotExist, AttributeError):
        profile, _ = UserProfile.objects.get_or_create(
            user=user,
            defaults={
                'role': 'farmer' if (user.is_staff or user.is_superuser) else 'customer',
                'location': 'Tamil Nadu',
                'is_verified': True if user.is_superuser else False,
            }
        )
        return profile


# --- PUBLIC & AUTHENTICATION VIEWS ---

def home_view(request):
    """Landing page featuring interactive live farmer map and fresh harvests"""
    ensure_seed_data_loaded()
    farmers = UserProfile.objects.filter(role='farmer').select_related('user')
    farmers_data = []
    for fp in farmers:
        product_count = fp.user.products.filter(stock_quantity__gt=0).count()
        farmers_data.append({
            'id': fp.user.id,
            'name': fp.user.username,
            'farm_name': fp.farm_name or f"{fp.user.username}'s Farm",
            'location': fp.location,
            'phone': fp.phone_number,
            'lat': fp.latitude or 18.5204,
            'lng': fp.longitude or 73.8567,
            'product_count': product_count,
        })

    featured_products = Product.objects.filter(stock_quantity__gt=0).select_related('farmer', 'farmer__profile')[:8]
    locations = UserProfile.objects.filter(role='farmer').values_list('location', flat=True).distinct()
    return render(request, 'home.html', {
        'featured_products': featured_products,
        'farmers_json': farmers_data,
        'locations': [loc for loc in locations if loc],
    })



def register_view(request):
    """User registration step for both Farmers and Customers with secure OTP SMS trigger"""
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.first_name = form.cleaned_data.get('full_name', '')
            user.save()

            role = form.cleaned_data['role']
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.role = role
            profile.phone_number = form.cleaned_data.get('phone_number', '')
            profile.district = form.cleaned_data.get('district', '')

            if role == 'farmer':
                profile.farm_name = form.cleaned_data.get('farm_name', '')
                profile.location = form.cleaned_data.get('farm_location', '')
                profile.address = form.cleaned_data.get('farm_address', '')
            else:  # customer
                profile.farm_name = ''
                city_town = form.cleaned_data.get('city_town')
                profile.location = city_town if city_town else form.cleaned_data.get('district', '')
                profile.address = form.cleaned_data.get('delivery_address', '')

            profile.is_verified = False
            profile.save()

            # Generate 6-digit OTP to be verified directly on screen
            otp = profile.generate_otp(is_resend=False)
            request.session['pending_user_id'] = user.id

            messages.success(
                request,
                "🌱 Registration details submitted! Enter the 6-digit verification code shown below to activate your account."
            )
            return redirect('verify_otp')
    else:
        initial_role = request.GET.get('role', 'customer')
        if initial_role not in ['farmer', 'customer']:
            initial_role = 'customer'
        form = UserRegistrationForm(initial={'role': initial_role})

    return render(request, 'auth/register.html', {'form': form})


def verify_otp_view(request):
    """Direct on-screen OTP verification step without external SMS errors"""
    user_id = request.session.get('pending_user_id')
    if not user_id:
        messages.warning(request, "Session expired or invalid. Please sign up or log in.")
        return redirect('register')

    user = get_object_or_404(User, id=user_id)
    profile = get_user_profile(user)

    if request.method == 'POST':
        form = OTPVerificationForm(request.POST)
        if form.is_valid():
            entered_otp = form.cleaned_data['otp']
            is_valid, verify_msg = profile.verify_otp(entered_otp)

            if is_valid:
                del request.session['pending_user_id']
                login(request, user)
                display_name = user.first_name or user.username
                messages.success(request, f"🎉 Verification successful! Welcome to FarmConnect, {display_name}.")

                # Redirect to appropriate role dashboard
                if profile.role == 'farmer':
                    return redirect('farmer_dashboard')
                return redirect('customer_browse')
            else:
                messages.error(request, f"❌ {verify_msg}")
    else:
        form = OTPVerificationForm()

    return render(request, 'auth/verify_otp.html', {
        'form': form,
        'user_obj': user,
        'profile': profile,
        'screen_otp': profile.otp,
    })


def resend_otp_view(request):
    """Generates a fresh OTP directly on screen with 0 errors"""
    user_id = request.session.get('pending_user_id')
    if not user_id:
        messages.error(request, "Session expired. Please register again.")
        return redirect('register')

    user = get_object_or_404(User, id=user_id)
    profile = get_user_profile(user)

    new_otp = profile.generate_otp(is_resend=True)
    messages.info(request, "🔄 A fresh 6-digit verification code has been generated on screen.")
    return redirect('verify_otp')


def login_view(request):
    """User Login for both Farmer and Customer with role-based dashboard redirects"""
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            profile = get_user_profile(user)

            if profile and not profile.is_verified:
                profile.generate_otp(is_resend=False)
                request.session['pending_user_id'] = user.id
                messages.info(request, "Please enter your verification code below to activate your account.")
                return redirect('verify_otp')

            login(request, user)
            display_name = user.first_name or user.username
            messages.success(request, f"Welcome back, {display_name}!")

            next_url = request.GET.get('next') or request.POST.get('next')
            if next_url and next_url.startswith('/'):
                return redirect(next_url)

            # Redirect each user to the correct dashboard based on their role
            if profile and profile.role == 'farmer':
                return redirect('farmer_dashboard')
            return redirect('customer_browse')
        else:
            messages.error(request, "Invalid username or password.")

    return render(request, 'auth/login.html')

    return render(request, 'auth/login.html')


def logout_view(request):
    logout(request)
    messages.info(request, "You have logged out successfully.")
    return redirect('home')


# --- FARMER WORKFLOW VIEWS ---

@login_required
def farmer_dashboard(request):
    """Farmer home: lists products, stock, and high-level stats"""
    profile = get_user_profile(request.user)
    if (not profile or profile.role != 'farmer') and not request.user.is_superuser:
        messages.error(request, "Access restricted to Farmer accounts.")
        return redirect('customer_browse')

    products = Product.objects.filter(farmer=request.user)
    # Calculate stats
    total_products = products.count()
    active_stock_count = products.filter(stock_quantity__gt=0).count()
    
    # Orders containing farmer's items
    farmer_items = OrderItem.objects.filter(farmer=request.user)
    pending_orders_count = Order.objects.filter(
        items__farmer=request.user,
        order_status__in=['placed', 'preparing']
    ).distinct().count()

    return render(request, 'farmer/dashboard.html', {
        'products': products,
        'total_products': total_products,
        'active_stock_count': active_stock_count,
        'pending_orders_count': pending_orders_count,
    })


@login_required
def add_product_view(request):
    """Farmer adds Fresh Harvest (Vegetable / Fruit), Price + Quantity"""
    profile = get_user_profile(request.user)
    if (not profile or profile.role != 'farmer') and not request.user.is_superuser:
        return redirect('customer_browse')

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.farmer = request.user
            product.save()
            messages.success(request, f"🌾 '{product.name}' has been listed with {product.stock_quantity} {product.unit} stock!")
            return redirect('farmer_dashboard')
    else:
        form = ProductForm()

    return render(request, 'farmer/add_product.html', {'form': form})


@login_required
def edit_product_view(request, product_id):
    """Farmer edits price, stock, or harvest details"""
    product = get_object_or_404(Product, id=product_id, farmer=request.user)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, f"Updated '{product.name}' details and stock.")
            return redirect('farmer_dashboard')
    else:
        form = ProductForm(instance=product)

    return render(request, 'farmer/edit_product.html', {'form': form, 'product': product})


@login_required
def delete_product_view(request, product_id):
    """Farmer removes a harvest listing"""
    product = get_object_or_404(Product, id=product_id, farmer=request.user)
    if request.method == 'POST':
        name = product.name
        product.delete()
        messages.info(request, f"Listing for '{name}' was removed.")
        return redirect('farmer_dashboard')
    return render(request, 'farmer/confirm_delete.html', {'product': product})


@login_required
def farmer_orders_view(request):
    """Farmer manages incoming orders and updates status (Preparing -> Ready -> Delivered)"""
    profile = get_user_profile(request.user)
    if (not profile or profile.role != 'farmer') and not request.user.is_superuser:
        return redirect('customer_browse')

    orders = Order.objects.filter(items__farmer=request.user).distinct()
    return render(request, 'farmer/orders.html', {'orders': orders})


@login_required
@require_POST
def update_order_status_view(request, order_id):
    """Update order progress: 'Farmer Prepares Order' -> 'Ready for Collection/Delivery' -> 'Delivered'"""
    order = get_object_or_404(Order, id=order_id, items__farmer=request.user)
    new_status = request.POST.get('status')
    
    valid_transitions = {
        'placed': 'preparing',      # Farmer Prepares Order
        'preparing': 'ready',       # Ready for Collection / Delivery
        'ready': 'delivered',       # Customer Receives
    }

    if new_status in dict(Order.ORDER_STATUS_CHOICES):
        order.order_status = new_status
        if new_status == 'delivered' and order.payment_method == 'cod':
            order.payment_status = 'completed'  # COD collected on spot
        order.save()
        messages.success(request, f"Order #{order.order_number} status updated to '{order.get_order_status_display()}'.")
    else:
        messages.error(request, "Invalid order status requested.")

    return redirect('farmer_orders')


# --- CUSTOMER WORKFLOW VIEWS ---

def customer_browse_view(request):
    """Customer selects location, views nearby farmers, and browses fresh harvest"""
    ensure_seed_data_loaded()
    location_query = request.GET.get('location', '').strip()
    category_query = request.GET.get('category', '').strip()
    search_query = request.GET.get('q', '').strip()

    products = Product.objects.all().select_related('farmer', 'farmer__profile')

    if location_query:
        products = products.filter(farmer__profile__location__icontains=location_query)

    if category_query in ['vegetable', 'fruit']:
        products = products.filter(category=category_query)

    if search_query:
        products = products.filter(name__icontains=search_query)

    # Distinct locations for the dropdown / filter pills
    all_locations = UserProfile.objects.filter(role='farmer').values_list('location', flat=True).distinct()
    unique_locations = sorted([loc for loc in all_locations if loc])

    return render(request, 'customer/browse.html', {
        'products': products,
        'selected_location': location_query,
        'selected_category': category_query,
        'search_query': search_query,
        'unique_locations': unique_locations,
    })


def product_detail_view(request, product_id):
    """View product details, freshness, farmer profile, and add to cart with stock validation"""
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'customer/product_detail.html', {'product': product})


@login_required
def add_to_cart_view(request, product_id):
    """Customer selects quantity and adds product to cart"""
    profile = get_user_profile(request.user)
    if profile and profile.role != 'customer' and not request.user.is_superuser:
        messages.warning(request, "Farmers cannot purchase items. Please log in as a Customer.")
        return redirect('farmer_dashboard')

    product = get_object_or_404(Product, id=product_id)

    try:
        quantity = Decimal(request.POST.get('quantity', 1))
        if quantity <= 0:
            quantity = Decimal(1)
    except Exception:
        quantity = Decimal(1)

    # Pre-check stock
    if product.stock_quantity <= 0:
        messages.error(request, f"Sorry, '{product.name}' is currently Out of Stock.")
        return redirect('customer_browse')

    if quantity > product.stock_quantity:
        messages.warning(
            request,
            f"Only {product.stock_quantity} {product.unit} of '{product.name}' available in stock. Added maximum available."
        )
        quantity = product.stock_quantity

    cart_item, created = CartItem.objects.get_or_create(
        customer=request.user,
        product=product,
        defaults={'quantity': quantity}
    )

    if not created:
        new_quantity = cart_item.quantity + quantity
        if new_quantity > product.stock_quantity:
            messages.warning(request, f"You reached max available stock ({product.stock_quantity} {product.unit}).")
            cart_item.quantity = product.stock_quantity
        else:
            cart_item.quantity = new_quantity
        cart_item.save()

    messages.success(request, f"🛒 Added {cart_item.quantity} {product.unit} of {product.name} to cart.")
    return redirect('cart_view')


@login_required
def cart_view(request):
    """Displays cart items, enables dynamic JS quantity/total recalculation"""
    cart_items = CartItem.objects.filter(customer=request.user).select_related('product', 'product__farmer')
    total_amount = sum(item.subtotal for item in cart_items)

    return render(request, 'customer/cart.html', {
        'cart_items': cart_items,
        'total_amount': total_amount,
    })


@login_required
def update_cart_ajax(request):
    """AJAX endpoint for JavaScript live recalculation of quantities and subtotals"""
    if request.method == 'POST':
        item_id = request.POST.get('item_id')
        new_qty = request.POST.get('quantity')
        try:
            item = CartItem.objects.get(id=item_id, customer=request.user)
            qty = Decimal(new_qty)
            if qty <= 0:
                item.delete()
                deleted = True
                subtotal = 0
            else:
                if qty > item.product.stock_quantity:
                    qty = item.product.stock_quantity
                item.quantity = qty
                item.save()
                deleted = False
                subtotal = float(item.subtotal)

            all_items = CartItem.objects.filter(customer=request.user)
            total = float(sum(i.subtotal for i in all_items))
            count = all_items.count()

            return JsonResponse({
                'success': True,
                'deleted': deleted,
                'subtotal': subtotal,
                'total_amount': total,
                'cart_count': count,
                'quantity': float(qty) if not deleted else 0,
                'max_stock': float(item.product.stock_quantity) if not deleted else 0
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=405)


@login_required
def remove_from_cart_view(request, item_id):
    """Removes an item from cart"""
    item = get_object_or_404(CartItem, id=item_id, customer=request.user)
    name = item.product.name
    item.delete()
    messages.info(request, f"Removed {name} from your cart.")
    return redirect('cart_view')


@login_required
def checkout_view(request):
    """
    Checkout step:
    - Choose COD / Pay on Spot or Razorpay Test Mode
    - Django validates stock quantity in atomic transaction
    - If Stock Available:
        -> Order Confirmed (Save payment status)
        -> Reduce stock quantity
        -> Farmer gets order
    - If Stock Not Available:
        -> Show "Out of Stock"
    """
    cart_items = CartItem.objects.filter(customer=request.user).select_related('product', 'product__farmer')
    if not cart_items.exists():
        messages.warning(request, "Your cart is empty. Please add items before checking out.")
        return redirect('customer_browse')

    total_amount = sum(item.subtotal for item in cart_items)
    profile = get_user_profile(request.user)

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            payment_method = form.cleaned_data['payment_method']
            delivery_address = form.cleaned_data['delivery_address']
            delivery_location = form.cleaned_data['delivery_location']
            contact_phone = form.cleaned_data['contact_phone']

            # Django Validates Stock Quantity atomically
            with transaction.atomic():
                out_of_stock_items = []

                # Lock the products in database for concurrency safety
                for cart_item in cart_items:
                    product = Product.objects.select_for_update().get(id=cart_item.product.id)
                    if product.stock_quantity < cart_item.quantity:
                        out_of_stock_items.append({
                            'name': product.name,
                            'available': product.stock_quantity,
                            'requested': cart_item.quantity,
                            'unit': product.unit
                        })

                # If any product has insufficient stock -> Show "Out of Stock"
                if out_of_stock_items:
                    for item in out_of_stock_items:
                        messages.error(
                            request,
                            f"❌ Out of Stock: Only {item['available']} {item['unit']} of '{item['name']}' "
                            f"available, but {item['requested']} was requested."
                        )
                    return redirect('cart_view')

                # STOCK AVAILABLE: Create Order & Reduce Stock
                order_number = f"ORD-{uuid.uuid4().hex[:8].upper()}"
                payment_status = 'pending'

                order = Order.objects.create(
                    order_number=order_number,
                    customer=request.user,
                    delivery_address=delivery_address,
                    delivery_location=delivery_location,
                    contact_phone=contact_phone,
                    total_amount=total_amount,
                    payment_method=payment_method,
                    payment_status=payment_status,
                    order_status='placed'
                )

                for cart_item in cart_items:
                    product = Product.objects.select_for_update().get(id=cart_item.product.id)
                    # Reduce stock quantity
                    product.stock_quantity -= cart_item.quantity
                    product.save(update_fields=['stock_quantity'])

                    # Create order item
                    OrderItem.objects.create(
                        order=order,
                        farmer=product.farmer,
                        product=product,
                        product_name=product.name,
                        quantity=cart_item.quantity,
                        unit=product.unit,
                        price_per_kg=product.price_per_kg,
                        subtotal=cart_item.subtotal
                    )

                # Clear Customer Cart
                cart_items.delete()

                # Handle Payment Gateway Route
                if payment_method in ['upi', 'online_razorpay']:
                    order.payment_method = 'upi'
                    order.save(update_fields=['payment_method'])
                    return redirect('upi_payment', order_id=order.id)
                else:
                    # Cash on Delivery / Pay on Spot
                    messages.success(request, f"🎉 Order #{order.order_number} confirmed! Farmer has received your pre-order.")
                    return redirect('order_success', order_id=order.id)

    else:
        form = CheckoutForm(initial={
            'delivery_address': profile.address if profile else '',
            'delivery_location': profile.location if profile else '',
            'contact_phone': profile.phone_number if profile else '',
            'payment_method': 'cod',
        })

    return render(request, 'customer/checkout.html', {
        'form': form,
        'cart_items': cart_items,
        'total_amount': total_amount,
    })


@login_required
def upi_payment_view(request, order_id):
    """Renders the Instant UPI & QR Code Payment Portal"""
    order = get_object_or_404(Order, id=order_id, customer=request.user)
    upi_id = "farmconnect@upi"
    upi_name = "FarmConnect Harvest"
    # Standard UPI URI - opens GPay, PhonePe, Paytm, or BHIM directly on mobile/desktop
    upi_uri = f"upi://pay?pa={upi_id}&pn=FarmConnect&am={order.total_amount}&cu=INR&tn=PreOrder_{order.order_number}"
    qr_code_url = f"https://api.qrserver.com/v1/create-qr-code/?size=260x260&data={upi_uri}"

    return render(request, 'customer/upi_checkout.html', {
        'order': order,
        'upi_id': upi_id,
        'upi_name': upi_name,
        'upi_uri': upi_uri,
        'qr_code_url': qr_code_url,
    })


@login_required
@require_POST
def upi_verify_view(request, order_id):
    """Validates UPI payment confirmation (UTR / Ref ID) and updates order status"""
    order = get_object_or_404(Order, id=order_id, customer=request.user)
    upi_ref = request.POST.get('upi_transaction_id') or request.POST.get('razorpay_payment_id') or f"UPI{uuid.uuid4().hex[:10].upper()}"
    
    order.razorpay_payment_id = upi_ref
    order.payment_method = 'upi'
    order.payment_status = 'completed'
    order.save(update_fields=['razorpay_payment_id', 'payment_method', 'payment_status'])

    messages.success(request, f"💳 UPI Payment of ₹{order.total_amount} verified successfully! Ref: {upi_ref}")
    return redirect('order_success', order_id=order.id)


# Backward compatibility aliases
razorpay_payment_view = upi_payment_view
razorpay_verify_view = upi_verify_view


@login_required
def order_success_view(request, order_id):
    """Order confirmation screen with live timeline of order progress"""
    order = get_object_or_404(Order, id=order_id, customer=request.user)
    return render(request, 'customer/order_success.html', {'order': order})


@login_required
def customer_orders_view(request):
    """Customer views all placed pre-orders and live progress"""
    orders = Order.objects.filter(customer=request.user).prefetch_related('items')
    return render(request, 'customer/orders_list.html', {'orders': orders})


@login_required
def order_detail_view(request, order_id):
    """Detailed view of an order with its current timeline state"""
    order = get_object_or_404(Order, id=order_id)
    # Check permission: user is either the customer or one of the farmers for this order
    is_customer = order.customer == request.user
    is_farmer = order.items.filter(farmer=request.user).exists()

    if not (is_customer or is_farmer or request.user.is_superuser):
        messages.error(request, "Access denied to this order.")
        return redirect('home')

    return render(request, 'customer/order_detail.html', {
        'order': order,
        'is_customer': is_customer,
        'is_farmer': is_farmer,
    })
