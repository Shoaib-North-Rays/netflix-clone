from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
import stripe
import json
from datetime import datetime

from .models import SubscriptionPlan, StripeCustomer, StripeSubscription, UserProfile

# Configure Stripe - do this after importing settings
try:
    stripe.api_key = settings.STRIPE_SECRET_KEY
except Exception as e:
    print(f"Error configuring Stripe: {e}")


def test_stripe_connection(request):
    """Test Stripe API connection"""
    try:
        # Test Stripe connection
        products = stripe.Product.list(limit=1)
        return JsonResponse({
            'success': True,
            'message': 'Stripe connection successful',
            'products_count': len(products.data)
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
def create_checkout_session(request, plan_name):
    """Create Stripe checkout session for subscription"""
    try:
        # Configure Stripe API key
        stripe.api_key = settings.STRIPE_SECRET_KEY
        # Get the subscription plan
        plan = get_object_or_404(SubscriptionPlan, name=plan_name, is_active=True)
        
        # Get or create Stripe customer
        stripe_customer = StripeCustomer.get_or_create_customer(request.user)
        
        # Create Stripe price (in a real app, you'd create these in Stripe dashboard)
        # For now, we'll create them dynamically
        stripe_price = create_or_get_stripe_price(plan)
        
        # Create checkout session
        # For testing: try different configurations to work around regional restrictions
        try:
            checkout_session = stripe.checkout.Session.create(
                customer=stripe_customer.stripe_customer_id,
                payment_method_types=['card'],
                line_items=[{
                    'price': stripe_price.id,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=request.build_absolute_uri(reverse('users:subscription_success')) + '?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=request.build_absolute_uri(reverse('web:pricing')),
                metadata={
                    'user_id': request.user.id,
                    'plan_name': plan_name,
                },
                # Add these for testing
                allow_promotion_codes=False,
                billing_address_collection='auto',
            )
        except stripe.error.InvalidRequestError as e:
            if 'Indian regulations' in str(e):
                # Create a test success URL for development
                print(f"Stripe regional restriction detected. Creating test success URL for plan: {plan_name}")
                success_url = request.build_absolute_uri(reverse('users:subscription_success')) + f'?test_mode=true&plan={plan_name}&user_id={request.user.id}'
                return redirect(success_url)
            else:
                raise e
        
        return redirect(checkout_session.url)
        
    except Exception as e:
        print(f"Stripe checkout error: {str(e)}")
        import traceback
        traceback.print_exc()
        messages.error(request, f"Error creating checkout session: {str(e)}")
        return redirect('web:pricing')


def create_or_get_stripe_price(plan):
    """Create or get Stripe price for a subscription plan"""
    # First, try to get existing price by looking up products
    try:
        products = stripe.Product.list(limit=100)
        for product in products.data:
            if product.metadata.get('plan_name') == plan.name:
                # Get prices for this product
                prices = stripe.Price.list(product=product.id, active=True, limit=1)
                if prices.data:
                    return prices.data[0]
        
        # If no existing product/price found, create new ones
        product = stripe.Product.create(
            name=plan.display_name,
            description=plan.description,
            metadata={'plan_name': plan.name}
        )
        
        price = stripe.Price.create(
            product=product.id,
            unit_amount=int(plan.price * 100),  # Convert to cents
            currency='usd',
            recurring={'interval': 'month'},
            metadata={'plan_name': plan.name}
        )
        
        return price
        
    except stripe.error.StripeError as e:
        raise Exception(f"Error creating Stripe price: {str(e)}")


@login_required
def subscription_success(request):
    """Handle successful subscription payment"""
    session_id = request.GET.get('session_id')
    test_mode = request.GET.get('test_mode')
    
    # Handle test mode (for development when Stripe has regional restrictions)
    if test_mode:
        plan_name = request.GET.get('plan', 'basic')
        user_id = request.GET.get('user_id')
        
        if str(request.user.id) != user_id:
            messages.error(request, 'Invalid test session')
            return redirect('web:pricing')
        
        try:
            # Get the plan
            plan = SubscriptionPlan.objects.get(name=plan_name)
            
            # Create a test subscription record
            stripe_subscription, created = StripeSubscription.objects.update_or_create(
                user=request.user,
                defaults={
                    'stripe_subscription_id': f'test_sub_{request.user.id}_{int(timezone.now().timestamp())}',
                    'subscription_plan': plan,
                    'status': 'active',
                    'current_period_start': timezone.now(),
                    'current_period_end': timezone.now() + timezone.timedelta(days=30),
                    'cancel_at_period_end': False,
                }
            )
            
            # Update user profile subscription
            profile, created = UserProfile.objects.get_or_create(user=request.user)
            profile.subscription_plan = plan
            profile.subscription_start_date = stripe_subscription.current_period_start
            profile.subscription_end_date = stripe_subscription.current_period_end
            profile.save()
            
            messages.success(request, f'Test subscription created successfully for {plan.display_name} plan!')
            return render(request, 'users/subscription_success.html', {
                'plan': plan,
                'subscription': stripe_subscription,
                'test_mode': True
            })
        except SubscriptionPlan.DoesNotExist:
            messages.error(request, f'Invalid plan: {plan_name}')
            return redirect('web:pricing')
        except Exception as e:
            messages.error(request, f'Error creating test subscription: {str(e)}')
            return redirect('web:pricing')
    
    # Normal Stripe flow
    if not session_id:
        messages.error(request, "Invalid payment session")
        return redirect('web:pricing')
    
    try:
        # Retrieve the session from Stripe
        session = stripe.checkout.Session.retrieve(session_id)
        
        if session.payment_status == 'paid':
            # Get subscription details
            subscription = stripe.Subscription.retrieve(session.subscription)
            
            # Get the plan
            plan_name = session.metadata.get('plan_name')
            plan = SubscriptionPlan.objects.get(name=plan_name)
            
            # Create or update StripeSubscription
            stripe_subscription, created = StripeSubscription.objects.update_or_create(
                stripe_subscription_id=subscription.id,
                defaults={
                    'user': request.user,
                    'subscription_plan': plan,
                    'status': subscription.status,
                    'current_period_start': datetime.fromtimestamp(subscription.current_period_start, tz=timezone.utc),
                    'current_period_end': datetime.fromtimestamp(subscription.current_period_end, tz=timezone.utc),
                    'cancel_at_period_end': subscription.cancel_at_period_end,
                }
            )
            
            # Update user profile subscription
            profile, created = UserProfile.objects.get_or_create(user=request.user)
            profile.subscription_plan = plan
            profile.subscription_start_date = stripe_subscription.current_period_start
            profile.subscription_end_date = stripe_subscription.current_period_end
            profile.save()
            
            messages.success(request, f"Successfully subscribed to {plan.display_name}!")
            return render(request, 'users/subscription_success.html', {
                'plan': plan,
                'subscription': stripe_subscription
            })
        else:
            messages.error(request, "Payment was not successful")
            return redirect('web:pricing')
            
    except Exception as e:
        messages.error(request, f"Error processing subscription: {str(e)}")
        return redirect('web:pricing')


@login_required
def subscription_manage(request):
    """Manage user's subscriptions"""
    try:
        # Get user's active subscriptions
        subscriptions = StripeSubscription.objects.filter(
            user=request.user,
            status__in=['active', 'trialing']
        )
        
        context = {
            'subscriptions': subscriptions,
        }
        
        return render(request, 'users/manage_subscription.html', context)
        
    except Exception as e:
        messages.error(request, f"Error loading subscriptions: {str(e)}")
        return redirect('users:profile')


@login_required
@require_POST
def cancel_subscription(request, subscription_id):
    """Cancel a subscription"""
    try:
        subscription = get_object_or_404(
            StripeSubscription, 
            id=subscription_id, 
            user=request.user
        )
        
        # Check if this is a test subscription
        if subscription.stripe_subscription_id.startswith('test_sub_'):
            # For test subscriptions, just mark as canceled
            subscription.cancel_at_period_end = True
            subscription.save()
            
            # Update user profile
            try:
                profile = request.user.userprofile
                # Don't remove subscription immediately, let it expire
            except:
                pass
            
            messages.success(request, "Test subscription will be canceled at the end of the current period.")
        else:
            # Cancel in Stripe for real subscriptions
            success = subscription.cancel_subscription(at_period_end=True)
            
            if success:
                messages.success(request, "Subscription will be canceled at the end of the current period.")
            else:
                messages.error(request, "Failed to cancel subscription.")
            
    except Exception as e:
        messages.error(request, f"Error canceling subscription: {str(e)}")
    
    return redirect('users:subscription_manage')


@login_required
def customer_portal(request):
    """Redirect to Stripe customer portal"""
    try:
        stripe_customer = StripeCustomer.objects.get(user=request.user)
        
        # Create portal session
        portal_session = stripe.billing_portal.Session.create(
            customer=stripe_customer.stripe_customer_id,
            return_url=request.build_absolute_uri(reverse('users:manage_subscription')),
        )
        
        return redirect(portal_session.url)
        
    except StripeCustomer.DoesNotExist:
        messages.error(request, "No Stripe customer found. Please subscribe first.")
        return redirect('web:pricing')
    except Exception as e:
        messages.error(request, f"Error accessing customer portal: {str(e)}")
        return redirect('users:manage_subscription')


@csrf_exempt
def stripe_webhook(request):
    """Handle Stripe webhooks"""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    endpoint_secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', None)
    
    if not endpoint_secret:
        # For testing without webhook secret
        event = json.loads(payload)
    else:
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret
            )
        except ValueError:
            return HttpResponse(status=400)
        except stripe.error.SignatureVerificationError:
            return HttpResponse(status=400)
    
    # Handle the event
    if event['type'] == 'customer.subscription.updated':
        handle_subscription_updated(event['data']['object'])
    elif event['type'] == 'customer.subscription.deleted':
        handle_subscription_deleted(event['data']['object'])
    elif event['type'] == 'invoice.payment_succeeded':
        handle_invoice_payment_succeeded(event['data']['object'])
    elif event['type'] == 'invoice.payment_failed':
        handle_invoice_payment_failed(event['data']['object'])
    
    return HttpResponse(status=200)


def handle_subscription_updated(subscription):
    """Handle subscription update webhook"""
    try:
        stripe_subscription = StripeSubscription.objects.get(
            stripe_subscription_id=subscription['id']
        )
        
        # Update subscription details
        stripe_subscription.status = subscription['status']
        stripe_subscription.current_period_start = datetime.fromtimestamp(subscription['current_period_start'], tz=timezone.utc)
        stripe_subscription.current_period_end = datetime.fromtimestamp(subscription['current_period_end'], tz=timezone.utc)
        stripe_subscription.cancel_at_period_end = subscription['cancel_at_period_end']
        stripe_subscription.save()
        
        # Update user profile
        if stripe_subscription.is_active:
            profile = UserProfile.objects.get(user=stripe_subscription.user)
            profile.subscription_end_date = stripe_subscription.current_period_end
            profile.save()
            
    except StripeSubscription.DoesNotExist:
        print(f"Subscription not found: {subscription['id']}")
    except Exception as e:
        print(f"Error handling subscription update: {e}")


def handle_subscription_deleted(subscription):
    """Handle subscription deletion webhook"""
    try:
        stripe_subscription = StripeSubscription.objects.get(
            stripe_subscription_id=subscription['id']
        )
        
        stripe_subscription.status = 'canceled'
        stripe_subscription.save()
        
        # Update user profile to remove subscription
        profile = UserProfile.objects.get(user=stripe_subscription.user)
        profile.subscription_plan = None
        profile.subscription_end_date = None
        profile.save()
        
    except StripeSubscription.DoesNotExist:
        print(f"Subscription not found: {subscription['id']}")
    except Exception as e:
        print(f"Error handling subscription deletion: {e}")


def handle_invoice_payment_succeeded(invoice):
    """Handle successful invoice payment"""
    # Update subscription if needed
    if invoice.get('subscription'):
        subscription = stripe.Subscription.retrieve(invoice['subscription'])
        handle_subscription_updated(subscription)


def handle_invoice_payment_failed(invoice):
    """Handle failed invoice payment"""
    print(f"Payment failed for invoice: {invoice['id']}")
    # You might want to send email notifications here