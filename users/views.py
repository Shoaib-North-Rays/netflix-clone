from django.shortcuts import render, redirect
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from .forms import CustomUserCreationForm
from .models import UserProfile, SubscriptionPlan
from movies.models import Genre
from decimal import Decimal

def register(request):
    """User registration view with subscription plan selection"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Create user profile
            profile, created = UserProfile.objects.get_or_create(user=user)
            
            # Handle selected plan from form or URL params
            selected_plan = request.POST.get('selected_plan') or request.GET.get('plan', 'standard')
            
            # Store selected plan in session for subscription creation
            request.session['selected_plan'] = selected_plan
            
            # Login the user
            login(request, user)
            
            # Redirect to subscription page
            return redirect('users:subscribe', plan=selected_plan)
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'registration/register.html', {'form': form})

@login_required
def subscribe(request, plan):
    """Handle subscription creation and payment processing"""
    user = request.user
    
    # Get the subscription plan from database
    try:
        subscription_plan = SubscriptionPlan.objects.get(name=plan, is_active=True)
    except SubscriptionPlan.DoesNotExist:
        messages.error(request, 'Invalid subscription plan selected.')
        return redirect('web:pricing')
    
    if request.method == 'POST':
        # Process payment (this would integrate with Stripe/PayPal)
        # For now, we'll create a subscription directly
        
        try:
            # Get or create user profile
            user_profile, created = UserProfile.objects.get_or_create(user=user)
            
            # Set the subscription plan
            user_profile.subscription_plan = subscription_plan
            user_profile.subscription_start_date = timezone.now()
            user_profile.extend_subscription(subscription_plan.duration_days)
            user_profile.save()
            
            messages.success(request, f'Successfully subscribed to {subscription_plan.display_name} plan!')
            return redirect('web:home')
            
        except Exception as e:
            messages.error(request, f'There was an error processing your subscription: {str(e)}')
    
    context = {
        'plan': plan,
        'plan_info': subscription_plan,
    }
    
    return render(request, 'users/subscribe.html', context)


@login_required
def profile(request):
    """User profile page with account settings, subscription, and watch history"""
    user = request.user
    
    # Get or create user profile
    try:
        user_profile = user.profile
    except UserProfile.DoesNotExist:
        user_profile = UserProfile.objects.create(user=user)
    
    # Handle profile update
    if request.method == 'POST':
        # Update basic user information
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.phone = request.POST.get('phone', getattr(user, 'phone', ''))
        
        # Update date of birth if provided
        date_of_birth = request.POST.get('date_of_birth')
        if date_of_birth:
            try:
                from datetime import datetime
                user.date_of_birth = datetime.strptime(date_of_birth, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        # Update preferences
        preferred_language = request.POST.get('preferred_language')
        if preferred_language:
            user_profile.preferred_language = preferred_language
        
        preferred_genre_id = request.POST.get('preferred_genre')
        if preferred_genre_id:
            try:
                user_profile.preferred_genre = Genre.objects.get(id=preferred_genre_id)
            except Genre.DoesNotExist:
                user_profile.preferred_genre = None
        
        user.save()
        user_profile.save()
        
        messages.success(request, 'Profile updated successfully!')
        return redirect('users:profile')
    
    # Get watch history
    watch_history = []
    watch_history_count = 0
    if hasattr(user_profile, 'watchhistory_set'):
        watch_history = user_profile.watchhistory_set.all()[:10]  # Last 10 items
        watch_history_count = user_profile.watchhistory_set.count()
    
    # Get watchlist count
    watchlist_count = user_profile.watchlist.count()
    
    # Get all genres for preferences
    genres = Genre.objects.filter(is_active=True)
    
    context = {
        'watch_history': watch_history,
        'watch_history_count': watch_history_count,
        'watchlist_count': watchlist_count,
        'genres': genres,
    }
    
    return render(request, 'users/profile.html', context)


@login_required
def watch_history(request):
    """User watch history page"""
    user = request.user
    
    # Get or create user profile
    try:
        user_profile = user.profile
    except UserProfile.DoesNotExist:
        user_profile = UserProfile.objects.create(user=user)
    
    # Get watch history
    watch_history = []
    watch_history_count = 0
    completed_count = 0
    in_progress_count = 0
    total_watch_time = 0
    
    if hasattr(user_profile, 'watchhistory_set'):
        all_history = user_profile.watchhistory_set.all().order_by('-watched_at')
        watch_history = all_history[:50]  # Limit to 50 most recent
        watch_history_count = all_history.count()
        completed_count = all_history.filter(completed=True).count()
        in_progress_count = all_history.filter(completed=False).count()
        
        # Calculate total watch time
        for h in all_history:
            total_watch_time += h.watch_duration
        
        # Convert seconds to hours
        total_hours = total_watch_time // 3600
        total_watch_time = f"{total_hours}h" if total_hours > 0 else "0h"
    
    context = {
        'watch_history': watch_history,
        'watch_history_count': watch_history_count,
        'completed_count': completed_count,
        'in_progress_count': in_progress_count,
        'total_watch_time': total_watch_time,
        'has_more': watch_history_count > 50,
    }
    
    return render(request, 'users/watch_history.html', context)
