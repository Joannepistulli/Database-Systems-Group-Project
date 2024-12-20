from django.urls import path
from . import views

app_name = 'amazon_backend'

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('product/<str:product_id>/', views.product_detail, name='product_detail'),
    
    # Cart URLs
    path('cart/', views.view_cart, name='cart'),
    path('cart/add/<str:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<str:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/update/<str:product_id>/', views.update_cart_quantity, name='update_cart_quantity'),
    
    # Wishlist URLs
    path('wishlist/', views.view_wishlist, name='wishlist'),
    path('wishlist/add/<str:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/<str:product_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
    
    # Order URLs
    path('checkout/', views.checkout, name='checkout'),
    path('order-confirmation/<str:order_id>/', views.order_confirmation, name='order_confirmation'),
    path('my-orders/', views.my_orders, name='my_orders'),
    
    # Profile URLs
    path('profile/', views.profile, name='profile'),
    path('subscribe/', views.subscribe, name='subscribe'),
    path('subscription/cancel/', views.cancel_subscription, name='cancel_subscription'),
    
    # Vendor store URLs
    path('vendor/<str:vendor_id>/products/', views.vendor_store, name='vendor_store'),
]