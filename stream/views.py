from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse, Http404
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
import hashlib
import time
import os

from movies.models import Movie, VideoFile
from users.models import UserProfile


@login_required
def get_video_stream_url(request, movie_slug):
    """
    Generate secure streaming URL for authenticated users
    """
    movie = get_object_or_404(Movie, slug=movie_slug, is_active=True)
    
    # Check if user has active subscription
    try:
        user_profile = request.user.profile
        if not user_profile.is_subscription_active:
            return JsonResponse({
                'error': 'Active subscription required',
                'subscription_required': True
            }, status=403)
    except UserProfile.DoesNotExist:
        return JsonResponse({
            'error': 'User profile not found',
            'subscription_required': True
        }, status=403)
    
    # Get preferred quality or default
    requested_quality = request.GET.get('quality', 'auto')
    
    # Get available video files
    video_files = movie.video_files.filter(is_processed=True).order_by('-quality')
    
    if not video_files.exists():
        return JsonResponse({
            'error': 'No video files available for this movie'
        }, status=404)
    
    # Select appropriate quality
    if requested_quality == 'auto':
        selected_video = video_files.first()  # Highest quality available
    else:
        selected_video = video_files.filter(quality=requested_quality).first()
        if not selected_video:
            selected_video = video_files.first()  # Fallback to highest
    
    # Generate secure URL
    secure_url = generate_secure_video_url(
        request.user.id, 
        movie.id, 
        selected_video.id
    )
    
    # Track viewing
    track_video_access(request.user, movie)
    
    return JsonResponse({
        'success': True,
        'video_url': secure_url,
        'quality': selected_video.quality,
        'duration': selected_video.duration,
        'movie_title': movie.title,
        'expires_at': (timezone.now() + timedelta(hours=2)).isoformat()
    })


@login_required
def stream_video(request, video_token):
    """
    Stream video with secure token validation
    """
    # Validate token and get video file
    video_file = validate_and_get_video_file(request.user.id, video_token)
    
    if not video_file:
        raise Http404("Video not found or access denied")
    
    # Check file exists
    if not os.path.exists(video_file.file_path.path):
        return JsonResponse({
            'error': 'Video file not found on server'
        }, status=404)
    
    # Return video response
    return serve_video_file(request, video_file)


def generate_secure_video_url(user_id, movie_id, video_file_id):
    """
    Generate a secure, time-limited URL for video streaming
    """
    # Create token with expiry
    timestamp = int(time.time())
    expiry = timestamp + (2 * 60 * 60)  # 2 hours
    
    # Create hash
    token_data = f"{user_id}:{movie_id}:{video_file_id}:{expiry}"
    secret_key = getattr(settings, 'SECRET_KEY', 'default-secret')
    token_hash = hashlib.sha256(
        f"{token_data}:{secret_key}".encode()
    ).hexdigest()
    
    # Create secure token
    secure_token = f"{user_id}-{movie_id}-{video_file_id}-{expiry}-{token_hash}"
    
    return f"/api/stream/video/{secure_token}/"


def validate_and_get_video_file(user_id, token):
    """
    Validate secure token and return video file if valid
    """
    try:
        parts = token.split('-')
        if len(parts) != 5:
            return None
        
        token_user_id, movie_id, video_file_id, expiry, provided_hash = parts
        
        # Check if token is for the correct user
        if int(token_user_id) != user_id:
            return None
        
        # Check if token has expired
        if int(expiry) < int(time.time()):
            return None
        
        # Validate hash
        token_data = f"{token_user_id}:{movie_id}:{video_file_id}:{expiry}"
        secret_key = getattr(settings, 'SECRET_KEY', 'default-secret')
        expected_hash = hashlib.sha256(
            f"{token_data}:{secret_key}".encode()
        ).hexdigest()
        
        if provided_hash != expected_hash:
            return None
        
        # Get video file
        video_file = VideoFile.objects.get(
            id=int(video_file_id),
            movie_id=int(movie_id),
            is_processed=True
        )
        
        return video_file
    
    except (ValueError, VideoFile.DoesNotExist):
        return None


def serve_video_file(request, video_file):
    """
    Serve video file with range request support for seeking
    """
    file_path = video_file.file_path.path
    file_size = os.path.getsize(file_path)
    
    # Handle range requests for video seeking
    range_header = request.META.get('HTTP_RANGE', '').strip()
    range_re = r'bytes\s*=\s*(\d+)\s*-\s*(\d*)'
    
    if range_header:
        import re
        range_match = re.match(range_re, range_header)
        first_byte, last_byte = 0, None
        
        if range_match:
            first_byte, last_byte = range_match.groups()
            first_byte = int(first_byte)
            if last_byte:
                last_byte = int(last_byte)
    
    # Set response headers
    response = HttpResponse(content_type='video/mp4')
    response['Accept-Ranges'] = 'bytes'
    response['Content-Length'] = str(file_size)
    response['Cache-Control'] = 'no-cache, private'
    
    # Handle range request
    if range_header:
        response.status_code = 206  # Partial Content
        if last_byte is None:
            last_byte = file_size - 1
        
        response['Content-Range'] = f'bytes {first_byte}-{last_byte}/{file_size}'
        response['Content-Length'] = str(last_byte - first_byte + 1)
        
        # Read and return the requested range
        with open(file_path, 'rb') as video_file_obj:
            video_file_obj.seek(first_byte)
            response.content = video_file_obj.read(last_byte - first_byte + 1)
    else:
        # Return full file
        with open(file_path, 'rb') as video_file_obj:
            response.content = video_file_obj.read()
    
    return response


def track_video_access(user, movie):
    """
    Track user video access for analytics
    """
    from users.models import WatchHistory
    
    try:
        user_profile = user.profile
        
        # Update or create watch history
        watch_record, created = WatchHistory.objects.get_or_create(
            user_profile=user_profile,
            movie=movie,
            defaults={'watch_duration': 0}
        )
        
        if not created:
            # Update last watched time
            watch_record.watched_at = timezone.now()
            watch_record.save(update_fields=['watched_at'])
    
    except UserProfile.DoesNotExist:
        pass
