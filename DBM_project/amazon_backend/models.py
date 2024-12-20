import random
import string
from django.db import models
from django.contrib.auth.models import User
from datetime import datetime, timedelta

class Vendor(models.Model):
    vendor_id = models.CharField(max_length=20, primary_key=True)
    vendor_name = models.CharField(max_length=200)
    vendor_contact = models.CharField(max_length=20)
    
    def __str__(self):
        return self.vendor_name

class Product(models.Model):
    product_id = models.CharField(max_length=20, primary_key=True)
    vendor = models.ForeignKey(
        Vendor, 
        on_delete=models.CASCADE, 
        related_name='products',
        default='DEFAULT'
    )
    product_name = models.CharField(max_length=500)
    category = models.CharField(max_length=200)
    discounted_price = models.DecimalField(max_digits=10, decimal_places=2)
    actual_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_percentage = models.IntegerField()
    rating = models.DecimalField(max_digits=3, decimal_places=1)
    rating_count = models.CharField(max_length=20)
    about_product = models.TextField()
    img_link = models.URLField(max_length=500)
    product_link = models.URLField(max_length=500)
    stock = models.IntegerField(default=100)

    def __str__(self):
        return self.product_name

    class Meta:
        ordering = ['product_name']

class Review(models.Model):
    review_id = models.CharField(max_length=20, primary_key=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user_id = models.CharField(max_length=50)
    user_name = models.CharField(max_length=100)
    review_title = models.CharField(max_length=200)
    review_content = models.TextField()
    review_date = models.DateField()

    def __str__(self):
        return f"Review by {self.user_name} for {self.product.product_name}"

    class Meta:
        ordering = ['-review_date']

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product_id = models.CharField(max_length=100)
    product_name = models.CharField(max_length=500)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField(default=1)
    
    def __str__(self):
        return f"{self.quantity} x {self.product_name}"

class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product_id = models.CharField(max_length=100)
    product_name = models.CharField(max_length=500)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    def __str__(self):
        return f"{self.product_name}"

class Order(models.Model):
    ORDER_STATUS = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    )
    
    order_id = models.CharField(max_length=10, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=ORDER_STATUS, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Delivery Information
    full_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=10)
    
    # Payment Information (simplified)
    card_number = models.CharField(max_length=16)
    card_expiry = models.CharField(max_length=5)
    card_cvv = models.CharField(max_length=3)

    def __str__(self):
        return f"Order {self.order_id}"

    @staticmethod
    def generate_order_id():
        # Generate a random 10-character order ID
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product_id = models.CharField(max_length=20)
    product_name = models.CharField(max_length=500)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} x {self.product_name}"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    zip_code = models.CharField(max_length=10, blank=True)
    
    def __str__(self):
        return f"{self.user.username}'s profile"

class Subscription(models.Model):
    SUBSCRIPTION_STATUS = (
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled')
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField()
    next_payment_date = models.DateTimeField()
    status = models.CharField(max_length=10, choices=SUBSCRIPTION_STATUS, default='active')
    card_number = models.CharField(max_length=16)
    card_expiry = models.CharField(max_length=5)
    
    def save(self, *args, **kwargs):
        if not self.end_date:
            self.end_date = datetime.now() + timedelta(days=30)
        if not self.next_payment_date:
            self.next_payment_date = self.end_date
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.user.username}'s subscription"
