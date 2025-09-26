from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone
from datetime import datetime, timedelta
import stripe
from django.conf import settings

# Configure Stripe - will be done in views


class UserManager(BaseUserManager):
    def create_user(self, email, first_name, last_name, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        
        email = self.normalize_email(email)
        user = self.model(email=email, first_name=first_name, last_name=last_name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, first_name, last_name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, first_name, last_name, password, **extra_fields)


class User(AbstractUser):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    is_premium = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()


class SubscriptionPlan(models.Model):
    PLAN_TYPES = [
        ('free', 'Free'),
        ('basic', 'Basic'),
        ('standard', 'Standard'),
        ('premium', 'Premium'),
    ]
    
    name = models.CharField(max_length=50, choices=PLAN_TYPES, unique=True)
    display_name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_days = models.IntegerField(default=30)
    max_streams = models.IntegerField(default=1)
    hd_quality = models.BooleanField(default=False)
    ultra_hd_quality = models.BooleanField(default=False)
    download_allowed = models.BooleanField(default=False)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.display_name


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    subscription_plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True, blank=True)
    subscription_start_date = models.DateTimeField(null=True, blank=True)
    subscription_end_date = models.DateTimeField(null=True, blank=True)
    auto_renewal = models.BooleanField(default=True)
    watchlist = models.ManyToManyField('movies.Movie', blank=True, related_name='in_watchlists')
    watch_history = models.ManyToManyField('movies.Movie', through='WatchHistory', blank=True)
    preferred_language = models.CharField(max_length=10, default='en')
    preferred_genre = models.ForeignKey('movies.Genre', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} - Profile"

    @property
    def is_subscription_active(self):
        if not self.subscription_end_date:
            return False
        return self.subscription_end_date > timezone.now()

    def extend_subscription(self, days=30):
        if self.subscription_end_date and self.subscription_end_date > timezone.now():
            self.subscription_end_date += timedelta(days=days)
        else:
            self.subscription_end_date = timezone.now() + timedelta(days=days)
        self.save()


class WatchHistory(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    movie = models.ForeignKey('movies.Movie', on_delete=models.CASCADE)
    watched_at = models.DateTimeField(auto_now_add=True)
    watch_duration = models.IntegerField(default=0)  # in seconds
    completed = models.BooleanField(default=False)
    last_position = models.IntegerField(default=0)  # last watched position in seconds

    class Meta:
        unique_together = ['user_profile', 'movie']
        ordering = ['-watched_at']

    def __str__(self):
        return f"{self.user_profile.user.email} - {self.movie.title}"


class StripeCustomer(models.Model):
    """Store Stripe customer information"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='stripe_customer')
    stripe_customer_id = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} - {self.stripe_customer_id}"

    @classmethod
    def get_or_create_customer(cls, user):
        """Get existing customer or create new one in Stripe"""
        # Configure Stripe API key
        stripe.api_key = settings.STRIPE_SECRET_KEY
        
        try:
            stripe_customer = cls.objects.get(user=user)
            return stripe_customer
        except cls.DoesNotExist:
            # Create customer in Stripe
            customer = stripe.Customer.create(
                email=user.email,
                name=user.full_name,
                metadata={'user_id': user.id}
            )
            
            # Save in database
            stripe_customer = cls.objects.create(
                user=user,
                stripe_customer_id=customer.id
            )
            return stripe_customer


class StripeSubscription(models.Model):
    """Store Stripe subscription information"""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('canceled', 'Canceled'),
        ('incomplete', 'Incomplete'),
        ('incomplete_expired', 'Incomplete Expired'),
        ('past_due', 'Past Due'),
        ('paused', 'Paused'),
        ('trialing', 'Trialing'),
        ('unpaid', 'Unpaid'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stripe_subscriptions')
    stripe_subscription_id = models.CharField(max_length=255, unique=True)
    subscription_plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    current_period_start = models.DateTimeField()
    current_period_end = models.DateTimeField()
    cancel_at_period_end = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.subscription_plan.display_name if self.subscription_plan else 'Unknown'} ({self.status})"

    @property
    def is_active(self):
        return self.status in ['active', 'trialing']

    def cancel_subscription(self, at_period_end=True):
        """Cancel the subscription in Stripe"""
        try:
            stripe.Subscription.modify(
                self.stripe_subscription_id,
                cancel_at_period_end=at_period_end
            )
            self.cancel_at_period_end = at_period_end
            self.save()
            return True
        except stripe.error.StripeError as e:
            print(f"Error canceling subscription: {e}")
            return False


class PaymentMethod(models.Model):
    """Store user payment methods"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_methods')
    stripe_payment_method_id = models.CharField(max_length=255)
    card_brand = models.CharField(max_length=20, blank=True)
    card_last4 = models.CharField(max_length=4, blank=True)
    card_exp_month = models.IntegerField(null=True, blank=True)
    card_exp_year = models.IntegerField(null=True, blank=True)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_default', '-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.card_brand} ****{self.card_last4}"
