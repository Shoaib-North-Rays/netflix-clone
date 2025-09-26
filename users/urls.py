from django.urls import path
from . import views, stripe_views

app_name = 'users'

urlpatterns = [
    path('', views.register, name='register'),
    path('subscribe/<str:plan>/', views.subscribe, name='subscribe'),
    path('profile/', views.profile, name='profile'),
    path('watch-history/', views.watch_history, name='watch_history'),
    
    # Stripe payment URLs
    path('checkout/<str:plan_name>/', stripe_views.create_checkout_session, name='stripe_checkout'),
    path('subscription/success/', stripe_views.subscription_success, name='subscription_success'),
    path('subscription/manage/', stripe_views.subscription_manage, name='manage_subscription'),
    path('subscription/cancel/<int:subscription_id>/', stripe_views.cancel_subscription, name='cancel_subscription'),
    path('customer-portal/', stripe_views.customer_portal, name='customer_portal'),
    path('stripe/webhook/', stripe_views.stripe_webhook, name='stripe_webhook'),
    path('stripe/test/', stripe_views.test_stripe_connection, name='stripe_test'),
]
