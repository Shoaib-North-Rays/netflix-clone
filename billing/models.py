from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal

User = get_user_model()


class Payment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('stripe', 'Stripe'),
        ('paypal', 'PayPal'),
        ('credit_card', 'Credit Card'),
        ('bank_transfer', 'Bank Transfer'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    subscription_plan = models.ForeignKey('users.SubscriptionPlan', on_delete=models.CASCADE)
    
    # Payment details
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    
    # External payment service IDs
    transaction_id = models.CharField(max_length=200, unique=True)
    stripe_payment_intent_id = models.CharField(max_length=200, blank=True)
    stripe_customer_id = models.CharField(max_length=200, blank=True)
    
    # Metadata
    description = models.TextField(blank=True)
    failure_reason = models.TextField(blank=True)
    receipt_url = models.URLField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.email} - ${self.amount} - {self.status}"
    
    class Meta:
        ordering = ['-created_at']
    
    def mark_as_completed(self):
        self.status = 'completed'
        self.paid_at = timezone.now()
        self.save()
        
        # Extend user subscription
        user_profile = self.user.profile
        user_profile.subscription_plan = self.subscription_plan
        user_profile.extend_subscription(days=self.subscription_plan.duration_days)
        user_profile.save()
    
    def mark_as_failed(self, reason=""):
        self.status = 'failed'
        self.failure_reason = reason
        self.save()


class Invoice(models.Model):
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE, related_name='invoice')
    invoice_number = models.CharField(max_length=50, unique=True)
    issued_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField()
    
    # Billing details
    billing_name = models.CharField(max_length=200)
    billing_email = models.EmailField()
    billing_address = models.TextField()
    billing_city = models.CharField(max_length=100)
    billing_state = models.CharField(max_length=100)
    billing_postal_code = models.CharField(max_length=20)
    billing_country = models.CharField(max_length=100)
    
    # Tax information
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=4, default=Decimal('0.0000'))
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"Invoice {self.invoice_number}"
    
    def save(self, *args, **kwargs):
        if not self.invoice_number:
            # Generate invoice number
            import uuid
            self.invoice_number = f"INV-{timezone.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        
        # Calculate totals
        self.tax_amount = self.subtotal * self.tax_rate
        self.total_amount = self.subtotal + self.tax_amount
        
        super().save(*args, **kwargs)


class Subscription(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
        ('suspended', 'Suspended'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.ForeignKey('users.SubscriptionPlan', on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Subscription period
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    auto_renew = models.BooleanField(default=True)
    
    # Stripe subscription details
    stripe_subscription_id = models.CharField(max_length=200, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.email} - {self.plan.display_name} - {self.status}"
    
    class Meta:
        ordering = ['-created_at']
    
    @property
    def is_active(self):
        return self.status == 'active' and self.end_date > timezone.now()
    
    def cancel(self):
        self.status = 'cancelled'
        self.cancelled_at = timezone.now()
        self.auto_renew = False
        self.save()
    
    def suspend(self):
        self.status = 'suspended'
        self.save()
    
    def reactivate(self):
        if self.end_date > timezone.now():
            self.status = 'active'
            self.save()
        else:
            self.status = 'expired'
