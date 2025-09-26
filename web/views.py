from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from movies.models import Movie, Genre, Actor, TVShow, Season, Episode
from users.models import UserProfile


def home(request):
    """Netflix-style home page with featured content"""
    # Get featured movies
    featured_movies = Movie.objects.filter(is_featured=True, is_active=True)[:5]
    
    # Get trending movies
    trending_movies = Movie.objects.filter(is_trending=True, is_active=True)[:10]
    
    # Get new releases
    new_releases = Movie.objects.filter(is_new_release=True, is_active=True)[:10]
    
    # Get movies by genre
    action_movies = Movie.objects.filter(genres__name__icontains='Action', is_active=True)[:10]
    comedy_movies = Movie.objects.filter(genres__name__icontains='Comedy', is_active=True)[:10]
    drama_movies = Movie.objects.filter(genres__name__icontains='Drama', is_active=True)[:10]
    
    # Get TV Shows
    featured_tvshows = TVShow.objects.filter(is_featured=True, is_active=True)[:5]
    trending_tvshows = TVShow.objects.filter(is_trending=True, is_active=True)[:10]
    ongoing_tvshows = TVShow.objects.filter(status='ongoing', is_active=True)[:10]
    
    # Get hero content (prefer TV show, fallback to movie)
    hero_content = None
    hero_type = 'movie'
    if featured_tvshows.exists():
        hero_content = featured_tvshows.first()
        hero_type = 'tvshow'
    elif featured_movies.exists():
        hero_content = featured_movies.first()
        hero_type = 'movie'
    
    context = {
        'hero_content': hero_content,
        'hero_type': hero_type,
        'hero_movie': featured_movies.first() if featured_movies.exists() else None,  # For backward compatibility
        'featured_movies': featured_movies,
        'trending_movies': trending_movies,
        'new_releases': new_releases,
        'action_movies': action_movies,
        'comedy_movies': comedy_movies,
        'drama_movies': drama_movies,
        'featured_tvshows': featured_tvshows,
        'trending_tvshows': trending_tvshows,
        'ongoing_tvshows': ongoing_tvshows,
    }
    
    return render(request, 'web/home.html', context)


def movies(request):
    """Movies catalog page with filtering and pagination"""
    movies_list = Movie.objects.filter(is_active=True)
    
    # Get filter parameters
    genre_filter = request.GET.get('genre')
    search_query = request.GET.get('search')
    sort_by = request.GET.get('sort', '-created_at')
    
    # Apply filters
    if genre_filter:
        movies_list = movies_list.filter(genres__slug=genre_filter)
    
    if search_query:
        movies_list = movies_list.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(actors__name__icontains=search_query)
        ).distinct()
    
    # Apply sorting
    movies_list = movies_list.order_by(sort_by)
    
    # Pagination
    paginator = Paginator(movies_list, 20)
    page_number = request.GET.get('page')
    movies_page = paginator.get_page(page_number)
    
    # Get genres for filter dropdown
    genres = Genre.objects.filter(is_active=True)
    
    context = {
        'movies': movies_page,
        'genres': genres,
        'current_genre': genre_filter,
        'search_query': search_query,
        'sort_by': sort_by,
    }
    
    return render(request, 'web/movies.html', context)


def movie_detail(request, slug):
    """Individual movie detail page"""
    movie = get_object_or_404(Movie, slug=slug, is_active=True)
    
    # Increment view count
    movie.increment_view_count()
    
    # Get related movies (same genre)
    related_movies = Movie.objects.filter(
        genres__in=movie.genres.all(),
        is_active=True
    ).exclude(id=movie.id).distinct()[:6]
    
    # Check if user can watch (has active subscription)
    can_watch = False
    if request.user.is_authenticated:
        try:
            user_profile = request.user.profile
            can_watch = user_profile.is_subscription_active
        except UserProfile.DoesNotExist:
            pass
    
    # Check if movie is in user's watchlist
    in_watchlist = False
    if request.user.is_authenticated:
        try:
            user_profile = request.user.profile
            in_watchlist = movie in user_profile.watchlist.all()
        except UserProfile.DoesNotExist:
            pass
    
    context = {
        'movie': movie,
        'related_movies': related_movies,
        'can_watch': can_watch,
        'in_watchlist': in_watchlist,
    }
    
    return render(request, 'web/movie_detail.html', context)


@login_required
def watch_movie(request, slug):
    """Movie player page"""
    movie = get_object_or_404(Movie, slug=slug, is_active=True)
    
    # Check if user has active subscription
    try:
        user_profile = request.user.profile
        if not user_profile.is_subscription_active:
            return render(request, 'web/subscription_required.html', {'movie': movie})
    except UserProfile.DoesNotExist:
        return render(request, 'web/subscription_required.html', {'movie': movie})
    
    # Get video files for different qualities
    video_files = movie.video_files.filter(is_processed=True)
    
    context = {
        'movie': movie,
        'video_files': video_files,
    }
    
    return render(request, 'web/watch.html', context)


@login_required
def toggle_watchlist(request, movie_id):
    """AJAX endpoint to add/remove movie from watchlist"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    movie = get_object_or_404(Movie, id=movie_id, is_active=True)
    
    try:
        user_profile = request.user.profile
    except UserProfile.DoesNotExist:
        # Create profile if it doesn't exist
        user_profile = UserProfile.objects.create(user=request.user)
    
    if movie in user_profile.watchlist.all():
        user_profile.watchlist.remove(movie)
        in_watchlist = False
        action = 'removed'
    else:
        user_profile.watchlist.add(movie)
        in_watchlist = True
        action = 'added'
    
    return JsonResponse({
        'success': True,
        'in_watchlist': in_watchlist,
        'action': action
    })


@login_required
def my_list(request):
    """User's watchlist page"""
    try:
        user_profile = request.user.profile
        watchlist_movies = user_profile.watchlist.filter(is_active=True)
    except UserProfile.DoesNotExist:
        watchlist_movies = []
    
    context = {
        'movies': watchlist_movies,
    }
    
    return render(request, 'web/my_list.html', context)


def pricing(request):
    """Subscription pricing page"""
    from users.models import SubscriptionPlan
    
    # Get active subscription plans from database
    plans = SubscriptionPlan.objects.filter(is_active=True).order_by('price')
    
    context = {
        'plans': plans,
    }
    
    return render(request, 'pricing.html', context)


# TV SHOW VIEWS
def tvshows(request):
    """TV Shows catalog page with filtering and pagination"""
    tvshows_list = TVShow.objects.filter(is_active=True)
    
    # Get filter parameters
    genre_filter = request.GET.get('genre')
    search_query = request.GET.get('search')
    status_filter = request.GET.get('status')
    sort_by = request.GET.get('sort', '-created_at')
    
    # Apply filters
    if genre_filter:
        tvshows_list = tvshows_list.filter(genres__slug=genre_filter)
    
    if status_filter:
        tvshows_list = tvshows_list.filter(status=status_filter)
    
    if search_query:
        tvshows_list = tvshows_list.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(actors__name__icontains=search_query)
        ).distinct()
    
    # Apply sorting
    if sort_by == 'rating':
        tvshows_list = tvshows_list.order_by('-imdb_rating')
    elif sort_by == 'year':
        tvshows_list = tvshows_list.order_by('-first_air_date')
    elif sort_by == 'title':
        tvshows_list = tvshows_list.order_by('title')
    else:
        tvshows_list = tvshows_list.order_by(sort_by)
    
    # Pagination
    paginator = Paginator(tvshows_list, 20)
    page_number = request.GET.get('page')
    tvshows_page = paginator.get_page(page_number)
    
    # Get genres and status choices for filters
    genres = Genre.objects.filter(is_active=True)
    status_choices = TVShow.STATUS_CHOICES
    
    context = {
        'tvshows': tvshows_page,
        'genres': genres,
        'status_choices': status_choices,
        'current_genre': genre_filter,
        'current_status': status_filter,
        'search_query': search_query,
        'sort_by': sort_by,
    }
    
    return render(request, 'web/tvshows.html', context)


def tvshow_detail(request, slug):
    """Individual TV show detail page"""
    tvshow = get_object_or_404(TVShow, slug=slug, is_active=True)
    
    # Increment view count
    tvshow.increment_view_count()
    
    # Get all seasons with episodes
    seasons = tvshow.seasons.filter(is_active=True).prefetch_related('episodes').order_by('season_number')
    
    # Get latest episode for 'Play Latest' button
    latest_episode = None
    if seasons.exists():
        latest_season = seasons.last()
        if latest_season.episodes.exists():
            latest_episode = latest_season.episodes.filter(is_active=True).last()
    
    # Get related TV shows (same genre)
    related_tvshows = TVShow.objects.filter(
        genres__in=tvshow.genres.all(),
        is_active=True
    ).exclude(id=tvshow.id).distinct()[:6]
    
    # Check if user can watch (has active subscription)
    can_watch = False
    if request.user.is_authenticated:
        try:
            user_profile = request.user.profile
            can_watch = user_profile.is_subscription_active
        except UserProfile.DoesNotExist:
            pass
    
    # Check if TV show is in user's TV show watchlist
    in_watchlist = False
    if request.user.is_authenticated:
        try:
            user_profile = request.user.profile
            # Check if the user profile has a tvshow_watchlist field, if not fall back to watchlist
            if hasattr(user_profile, 'tvshow_watchlist'):
                in_watchlist = tvshow in user_profile.tvshow_watchlist.all()
            else:
                # For now, we'll use the same watchlist field
                in_watchlist = False
        except UserProfile.DoesNotExist:
            pass
    
    context = {
        'tvshow': tvshow,
        'seasons': seasons,
        'latest_episode': latest_episode,
        'related_tvshows': related_tvshows,
        'can_watch': can_watch,
        'in_watchlist': in_watchlist,
    }
    
    return render(request, 'web/tvshow_detail.html', context)


@login_required
def watch_episode(request, show_slug, season_number, episode_number):
    """Episode player page"""
    tvshow = get_object_or_404(TVShow, slug=show_slug, is_active=True)
    season = get_object_or_404(Season, tvshow=tvshow, season_number=season_number, is_active=True)
    episode = get_object_or_404(Episode, season=season, episode_number=episode_number, is_active=True)
    
    # Check if user has active subscription
    try:
        user_profile = request.user.profile
        if not user_profile.is_subscription_active:
            return render(request, 'web/subscription_required.html', {
                'tvshow': tvshow,
                'episode': episode,
                'type': 'episode'
            })
    except UserProfile.DoesNotExist:
        return render(request, 'web/subscription_required.html', {
            'tvshow': tvshow,
            'episode': episode,
            'type': 'episode'
        })
    
    # Increment view count for episode
    episode.increment_view_count()
    
    # Get video file (Episode model has video_file, not video_files)
    video_files = []
    if episode.video_file and episode.is_processed:
        # Create a mock video files structure for template compatibility
        video_files = [{
            'file': episode.video_file,
            'quality': 'HD'
        }]
    
    # Get next and previous episodes for navigation
    next_episode = Episode.objects.filter(
        season__tvshow=tvshow,
        season__season_number=season_number,
        episode_number__gt=episode_number,
        is_active=True
    ).first()
    
    if not next_episode:
        # Check next season's first episode
        next_season = Season.objects.filter(
            tvshow=tvshow,
            season_number__gt=season_number,
            is_active=True
        ).first()
        if next_season:
            next_episode = next_season.episodes.filter(is_active=True).first()
    
    prev_episode = Episode.objects.filter(
        season__tvshow=tvshow,
        season__season_number=season_number,
        episode_number__lt=episode_number,
        is_active=True
    ).last()
    
    if not prev_episode:
        # Check previous season's last episode
        prev_season = Season.objects.filter(
            tvshow=tvshow,
            season_number__lt=season_number,
            is_active=True
        ).last()
        if prev_season:
            prev_episode = prev_season.episodes.filter(is_active=True).last()
    
    # Get all episodes in current season for episode list
    season_episodes = season.episodes.filter(is_active=True).order_by('episode_number')
    
    context = {
        'tvshow': tvshow,
        'season': season,
        'episode': episode,
        'video_files': video_files,
        'next_episode': next_episode,
        'prev_episode': prev_episode,
        'season_episodes': season_episodes,
    }
    
    return render(request, 'web/watch_episode.html', context)


@login_required
def toggle_tvshow_watchlist(request, tvshow_id):
    """AJAX endpoint to add/remove TV show from watchlist"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    tvshow = get_object_or_404(TVShow, id=tvshow_id, is_active=True)
    
    try:
        user_profile = request.user.profile
    except UserProfile.DoesNotExist:
        # Create profile if it doesn't exist
        user_profile = UserProfile.objects.create(user=request.user)
    
    # For now, we'll use a simple approach - you might want to create a separate tvshow_watchlist field
    # For this implementation, we'll create a simple way to track TV show watchlists
    
    # Check if user has this show in watchlist (we'll store it as a simple relationship)
    # This is a simplified approach - in a real app you might want separate watchlist models
    in_watchlist = False  # Placeholder - implement based on your user model structure
    
    return JsonResponse({
        'success': True,
        'in_watchlist': in_watchlist,
        'action': 'added' if in_watchlist else 'removed'
    })
