from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, SubscriptionPlan, UserProfile, WatchHistory, StripeCustomer, StripeSubscription, PaymentMethod


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'is_premium', 'is_active', 'date_joined')
    list_filter = ('is_premium', 'is_active', 'is_staff', 'date_joined')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'phone', 'date_of_birth', 'profile_picture')}),
        ('Permissions', {'fields': ('is_active', 'is_premium', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2'),
        }),
    )


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('display_name', 'name', 'price', 'duration_days', 'max_streams', 'is_active')
    list_filter = ('is_active', 'hd_quality', 'ultra_hd_quality', 'download_allowed')
    search_fields = ('display_name', 'name')
    ordering = ('price',)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'subscription_plan', 'subscription_end_date', 'is_subscription_active')
    list_filter = ('subscription_plan', 'auto_renewal')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    raw_id_fields = ('user',)
    filter_horizontal = ('watchlist',)


@admin.register(WatchHistory)
class WatchHistoryAdmin(admin.ModelAdmin):
    list_display = ('user_profile', 'movie', 'watched_at', 'watch_duration', 'completed')
    list_filter = ('completed', 'watched_at')
    search_fields = ('user_profile__user__email', 'movie__title')
    raw_id_fields = ('user_profile', 'movie')
    date_hierarchy = 'watched_at'


@admin.register(StripeCustomer)
class StripeCustomerAdmin(admin.ModelAdmin):
    list_display = ('user', 'stripe_customer_id', 'created_at')
    search_fields = ('user__email', 'stripe_customer_id')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(StripeSubscription)
class StripeSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'subscription_plan', 'status', 'current_period_start', 'current_period_end', 'cancel_at_period_end')
    list_filter = ('status', 'subscription_plan', 'cancel_at_period_end')
    search_fields = ('user__email', 'stripe_subscription_id')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'current_period_start'


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ('user', 'card_brand', 'card_last4', 'card_exp_month', 'card_exp_year', 'is_default')
    list_filter = ('card_brand', 'is_default')
    search_fields = ('user__email', 'card_last4')
