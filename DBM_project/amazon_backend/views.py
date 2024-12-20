import pandas as pd
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, Http404
from django.contrib.auth.models import User
from .models import Cart, Wishlist, Order, OrderItem, UserProfile, Subscription, Vendor
from django.core.paginator import Paginator
from django.contrib import messages
from datetime import datetime, timedelta
import urllib.parse
from decimal import Decimal
from django.utils import timezone
import os
from django.conf import settings

CSV_PATH = os.path.join(settings.BASE_DIR, 'amazon_backend', 'data', 'amazon.csv')

def load_products():
    try:
        df = pd.read_csv(CSV_PATH)
        return df.drop_duplicates(subset=['product_id'])
    except Exception as e:
        print(f"Error loading CSV: {e}")
        return pd.DataFrame()

def product_list(request):
    df = pd.read_csv(CSV_PATH)
    
    # Get selected category and properly decode it
    selected_category = request.GET.get('category')
    if selected_category:
        selected_category = urllib.parse.unquote_plus(selected_category)
    
    # Get filters
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    rating_filter = request.GET.get('rating_filter')
    
    # Get unique categories for the filter
    categories = sorted(df['category'].unique())
    
    # Filter by category if one is selected
    if selected_category:
        df = df[df['category'] == selected_category]
    
    # Clean and convert price data
    df['discounted_price'] = df['discounted_price'].apply(lambda x: float(str(x).replace('$', '').replace(',', '')) if pd.notnull(x) else 0)
    
    # Clean and convert rating data
    df['rating'] = pd.to_numeric(df['rating'], errors='coerce')
    
    # Filter by price range
    if min_price and min_price.strip():
        try:
            min_price_float = float(min_price)
            df = df[df['discounted_price'] >= min_price_float]
        except ValueError:
            min_price = ''
    
    if max_price and max_price.strip():
        try:
            max_price_float = float(max_price)
            df = df[df['discounted_price'] <= max_price_float]
        except ValueError:
            max_price = ''
    
    # Filter by rating
    if rating_filter and rating_filter.strip():
        try:
            rating_threshold = int(rating_filter)
            # Only show products with ratings >= the threshold
            df = df[df['rating'] >= float(rating_threshold)]
        except ValueError:
            rating_filter = ''
    
    # Remove duplicates based on product_id
    df = df.drop_duplicates(subset=['product_id'])
    
    # Get wishlist items for the current user
    wishlist_items = Wishlist.objects.filter(user=get_default_user()).values_list('product_id', flat=True)
    
    # Convert to list of dictionaries
    products = df.to_dict('records')
    
    # Pagination
    page_number = request.GET.get('page', 1)
    items_per_page = 12  # Show 12 products per page
    paginator = Paginator(products, items_per_page)
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'amazon_backend/product_list.html', {
        'products': page_obj,
        'categories': categories,
        'selected_category': selected_category,
        'page_obj': page_obj,
        'wishlist_items': wishlist_items,
        'min_price': min_price or '',
        'max_price': max_price or '',
        'rating_filter': rating_filter or ''
    })

def product_detail(request, product_id):
    df = pd.read_csv(CSV_PATH)
    
    try:
        # Get product info
        product = df[df['product_id'] == product_id].iloc[0].to_dict()
        reviews = df[df['product_id'] == product_id].to_dict('records')
        
        # Get vendor info directly from the same row
        vendor = {
            'vendor_id': product['vendor_id'],
            'vendor_name': product['vendor_name'],
            'vendor_contact': product['vendor_contact']
        }
        
    except IndexError:
        raise Http404("Product not found")
    
    context = {
        'product': product,
        'reviews': reviews,
        'vendor': vendor
    }
    return render(request, 'amazon_backend/product_detail.html', context)

# Get or create a default user
def get_default_user():
    user, created = User.objects.get_or_create(username='default_user')
    return user

def clean_price(price_str):
    # Remove '$' and any other non-numeric characters except decimal point
    if isinstance(price_str, str):
        return float(price_str.replace('$', '').strip())
    return float(price_str)

def add_to_cart(request, product_id):
    if request.method == 'POST':
        df = pd.read_csv(CSV_PATH)
        product = df[df['product_id'] == product_id].iloc[0]
        
        # Clean the price data
        price = clean_price(product['discounted_price'])
        
        cart_item, created = Cart.objects.get_or_create(
            user=get_default_user(),
            product_id=product_id,
            defaults={
                'product_name': product['product_name'],
                'price': price
            }
        )
        
        if not created:
            cart_item.quantity += 1
            cart_item.save()
            
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'})

def remove_from_cart(request, product_id):
    Cart.objects.filter(user=get_default_user(), product_id=product_id).delete()
    return JsonResponse({'status': 'success'})

def view_cart(request):
    cart_items = Cart.objects.filter(user=get_default_user())
    
    # Calculate line totals for each item
    for item in cart_items:
        item.line_total = item.price * item.quantity
    
    total = sum(item.line_total for item in cart_items)
    
    return render(request, 'amazon_backend/cart.html', {
        'cart_items': cart_items,
        'total': total
    })

def add_to_wishlist(request, product_id):
    if request.method == 'POST':
        df = pd.read_csv(CSV_PATH)
        product = df[df['product_id'] == product_id].iloc[0]
        
        # Clean the price data
        price = clean_price(product['discounted_price'])
        
        Wishlist.objects.get_or_create(
            user=get_default_user(),
            product_id=product_id,
            defaults={
                'product_name': product['product_name'],
                'price': price
            }
        )
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'})

def remove_from_wishlist(request, product_id):
    Wishlist.objects.filter(user=get_default_user(), product_id=product_id).delete()
    return JsonResponse({'status': 'success'})

def view_wishlist(request):
    wishlist_items = Wishlist.objects.filter(user=get_default_user())
    return render(request, 'amazon_backend/wishlist.html', {
        'wishlist_items': wishlist_items
    })

def checkout(request):
    cart_items = Cart.objects.filter(user=get_default_user())
    user = get_default_user()
    
    # Check if user has active subscription
    has_active_subscription = Subscription.objects.filter(
        user=user,
        status='active',
        end_date__gt=timezone.now()
    ).exists()
    
    # Calculate totals
    subtotal = sum(item.price * item.quantity for item in cart_items)
    delivery_fee = Decimal('0.00') if has_active_subscription else Decimal('25.00')
    total_with_delivery = subtotal + delivery_fee
    
    if request.method == 'POST':
        # Create order with the total including delivery fee
        order = Order.objects.create(
            order_id=Order.generate_order_id(),
            user=get_default_user(),
            total_amount=total_with_delivery,  # Use total with delivery
            full_name=request.POST.get('full_name'),
            email=request.POST.get('email'),
            phone=request.POST.get('phone'),
            address=request.POST.get('address'),
            city=request.POST.get('city'),
            state=request.POST.get('state'),
            zip_code=request.POST.get('zip_code'),
            card_number=request.POST.get('card_number'),
            card_expiry=request.POST.get('card_expiry'),
            card_cvv=request.POST.get('card_cvv')
        )
        
        # Create order items
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product_id=item.product_id,
                product_name=item.product_name,
                quantity=item.quantity,
                price=item.price
            )
        
        # Clear the cart
        cart_items.delete()
        
        return redirect('amazon_backend:order_confirmation', order_id=order.order_id)
    
    return render(request, 'amazon_backend/checkout.html', {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'delivery_fee': delivery_fee,
        'total': total_with_delivery,
        'has_active_subscription': has_active_subscription
    })

def order_confirmation(request, order_id):
    order = Order.objects.get(order_id=order_id)
    return render(request, 'amazon_backend/order_confirmation.html', {'order': order})

def my_orders(request):
    orders = Order.objects.filter(user=get_default_user()).order_by('-created_at')
    return render(request, 'amazon_backend/my_orders.html', {'orders': orders})

def profile(request):
    user = get_default_user()
    profile, created = UserProfile.objects.get_or_create(user=user)
    subscription = Subscription.objects.filter(user=user).first()
    
    # Define benefits directly
    benefits = [
        {
            'title': 'Free Shipping',
            'description': 'Get free shipping on all orders, no minimum purchase required.'
        },
        {
            'title': 'Early Access',
            'description': 'Get early access to sales and new products.'
        },
        {
            'title': 'Private Sales',
            'description': 'Exclusive access to VIP-only sales and discounts.'
        },
        {
            'title': 'Priority Support',
            'description': '24/7 priority customer support for VIP members.'
        }
    ]
    
    if request.method == 'POST':
        # Update profile information
        profile.phone = request.POST.get('phone')
        profile.address = request.POST.get('address')
        profile.city = request.POST.get('city')
        profile.state = request.POST.get('state')
        profile.zip_code = request.POST.get('zip_code')
        profile.save()
        
        # Update user information
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.email = request.POST.get('email')
        user.save()
        
        messages.success(request, 'Profile updated successfully!')
        return redirect('amazon_backend:profile')
    
    return render(request, 'amazon_backend/profile.html', {
        'profile': profile,
        'subscription': subscription,
        'benefits': benefits,
        'user': user  # Pass the default user to the template
    })

def subscribe(request):
    user = get_default_user()
    
    # Check for existing subscription
    existing_subscription = Subscription.objects.filter(user=user).first()
    
    if request.method == 'POST':
        if existing_subscription:
            # Update existing subscription
            existing_subscription.status = 'active'
            existing_subscription.start_date = datetime.now()
            existing_subscription.end_date = datetime.now() + timedelta(days=30)
            existing_subscription.next_payment_date = datetime.now() + timedelta(days=30)
            existing_subscription.card_number = request.POST.get('card_number')
            existing_subscription.card_expiry = request.POST.get('card_expiry')
            existing_subscription.save()
        else:
            # Create new subscription
            Subscription.objects.create(
                user=user,
                card_number=request.POST.get('card_number'),
                card_expiry=request.POST.get('card_expiry'),
                end_date=datetime.now() + timedelta(days=30),
                next_payment_date=datetime.now() + timedelta(days=30)
            )
        messages.success(request, 'Successfully subscribed to VIP service!')
        return redirect('amazon_backend:profile')
    
    benefits = [
        {
            'title': 'Free Shipping',
            'description': 'Get free shipping on all orders, no minimum purchase required.'
        },
        {
            'title': 'Early Access',
            'description': 'Get early access to sales and new products.'
        },
        {
            'title': 'Private Sales',
            'description': 'Exclusive access to VIP-only sales and discounts.'
        },
        {
            'title': 'Priority Support',
            'description': '24/7 priority customer support for VIP members.'
        }
    ]
    
    return render(request, 'amazon_backend/subscribe.html', {
        'benefits': benefits,
        'is_resubscribe': existing_subscription is not None
    })

def cancel_subscription(request):
    user = get_default_user()
    subscription = get_object_or_404(Subscription, user=user)
    subscription.status = 'cancelled'
    subscription.save()
    messages.success(request, 'Subscription cancelled successfully.')
    return redirect('amazon_backend:profile')

def update_cart_quantity(request, product_id):
    if request.method == 'POST':
        try:
            quantity = int(request.POST.get('quantity', 1))
            if quantity > 0:
                cart_item = Cart.objects.get(
                    user=get_default_user(),
                    product_id=product_id
                )
                cart_item.quantity = quantity
                cart_item.save()
                return JsonResponse({'status': 'success'})
        except (Cart.DoesNotExist, ValueError):
            pass
    return JsonResponse({'status': 'error'})

def vendor_store(request, vendor_id):
    df = pd.read_csv(CSV_PATH)
    
    try:
        # Get vendor info from first product of this vendor
        vendor_products = df[df['vendor_id'] == vendor_id]
        if vendor_products.empty:
            raise Http404("Vendor not found")
            
        vendor = {
            'vendor_id': vendor_id,
            'vendor_name': vendor_products.iloc[0]['vendor_name'],
            'vendor_contact': vendor_products.iloc[0]['vendor_contact']
        }
        
        # Get all products for this vendor
        vendor_products = vendor_products.drop_duplicates(subset=['product_id'])
        products = vendor_products.to_dict('records')
        
        # Pagination
        page_number = request.GET.get('page', 1)
        items_per_page = 12
        paginator = Paginator(products, items_per_page)
        page_obj = paginator.get_page(page_number)
        
        # Get wishlist items for product display
        wishlist_items = Wishlist.objects.filter(user=get_default_user()).values_list('product_id', flat=True)
        
        return render(request, 'amazon_backend/vendor_store.html', {
            'vendor': vendor,
            'products': page_obj,
            'page_obj': page_obj,
            'wishlist_items': wishlist_items
        })
        
    except IndexError:
        raise Http404("Vendor not found")
