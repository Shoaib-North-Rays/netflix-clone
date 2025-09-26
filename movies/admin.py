from django.contrib import admin
from .models import (
    Movie, Genre, Actor, Director, VideoFile, MovieRating, MovieLike,
    TVShow, Season, Episode, TVShowRating, TVShowLike, EpisodeWatchHistory
)


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Actor)
class ActorAdmin(admin.ModelAdmin):
    list_display = ('name', 'nationality', 'birth_date', 'created_at')
    list_filter = ('nationality', 'created_at')
    search_fields = ('name', 'nationality')
    date_hierarchy = 'created_at'


@admin.register(Director)
class DirectorAdmin(admin.ModelAdmin):
    list_display = ('name', 'nationality', 'birth_date', 'created_at')
    list_filter = ('nationality', 'created_at')
    search_fields = ('name', 'nationality')
    date_hierarchy = 'created_at'


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ('title', 'release_year', 'duration_formatted', 'rating', 'imdb_rating', 'view_count', 'is_featured', 'is_active')
    list_filter = ('rating', 'release_year', 'is_featured', 'is_trending', 'is_new_release', 'is_active', 'created_at')
    search_fields = ('title', 'description')
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ('genres', 'actors', 'directors')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('title', 'slug', 'description', 'release_year', 'duration', 'rating', 'imdb_rating')
        }),
        ('Media', {
            'fields': ('thumbnail', 'banner_image', 'trailer_url', 'trailer_file')
        }),
        ('Relationships', {
            'fields': ('genres', 'actors', 'directors')
        }),
        ('Flags', {
            'fields': ('is_featured', 'is_trending', 'is_new_release', 'is_active')
        }),
        ('Stats', {
            'fields': ('view_count', 'like_count'),
            'classes': ('collapse',)
        })
    )


@admin.register(VideoFile)
class VideoFileAdmin(admin.ModelAdmin):
    list_display = ('movie', 'quality', 'file_size', 'is_processed', 'created_at')
    list_filter = ('quality', 'is_processed', 'created_at')
    search_fields = ('movie__title',)
    raw_id_fields = ('movie',)
    date_hierarchy = 'created_at'


@admin.register(MovieRating)
class MovieRatingAdmin(admin.ModelAdmin):
    list_display = ('movie', 'user', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('movie__title', 'user__email')
    raw_id_fields = ('user', 'movie')
    date_hierarchy = 'created_at'


@admin.register(MovieLike)
class MovieLikeAdmin(admin.ModelAdmin):
    list_display = ['user', 'movie', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__email', 'movie__title']


class SeasonInline(admin.TabularInline):
    model = Season
    extra = 0
    fields = ['season_number', 'title', 'air_date']


class EpisodeInline(admin.TabularInline):
    model = Episode
    extra = 0
    fields = ['episode_number', 'title', 'duration', 'air_date']


@admin.register(TVShow)
class TVShowAdmin(admin.ModelAdmin):
    list_display = ['title', 'first_air_date', 'status', 'rating', 'imdb_rating', 'is_featured', 'is_active']
    list_filter = ['status', 'rating', 'is_featured', 'is_trending', 'is_active', 'first_air_date']
    search_fields = ['title', 'description']
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ['genres', 'actors', 'directors']
    inlines = [SeasonInline]
    readonly_fields = ['view_count', 'like_count', 'total_seasons', 'total_episodes']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'description', 'status')
        }),
        ('Air Dates', {
            'fields': ('first_air_date', 'last_air_date')
        }),
        ('Media', {
            'fields': ('thumbnail', 'banner_image', 'trailer_url')
        }),
        ('Content Rating', {
            'fields': ('rating', 'imdb_rating')
        }),
        ('Relationships', {
            'fields': ('genres', 'actors', 'directors')
        }),
        ('Status Flags', {
            'fields': ('is_featured', 'is_trending', 'is_new_release', 'is_active')
        }),
        ('Statistics', {
            'fields': ('view_count', 'like_count', 'total_seasons', 'total_episodes'),
            'classes': ['collapse']
        })
    )


@admin.register(Season)
class SeasonAdmin(admin.ModelAdmin):
    list_display = ['tvshow', 'season_number', 'title', 'episode_count', 'air_date']
    list_filter = ['tvshow', 'air_date']
    search_fields = ['tvshow__title', 'title']
    inlines = [EpisodeInline]
    readonly_fields = ['episode_count']


@admin.register(Episode)
class EpisodeAdmin(admin.ModelAdmin):
    list_display = ['season', 'episode_number', 'title', 'duration', 'air_date', 'view_count']
    list_filter = ['season__tvshow', 'air_date', 'is_processed']
    search_fields = ['title', 'description', 'season__tvshow__title']
    readonly_fields = ['view_count']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('season', 'episode_number', 'title', 'description')
        }),
        ('Timing', {
            'fields': ('air_date', 'duration')
        }),
        ('Media Files', {
            'fields': ('thumbnail', 'video_file', 'hls_playlist')
        }),
        ('Status', {
            'fields': ('is_processed', 'view_count')
        })
    )


@admin.register(TVShowRating)
class TVShowRatingAdmin(admin.ModelAdmin):
    list_display = ['user', 'tvshow', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['user__email', 'tvshow__title']


@admin.register(TVShowLike)
class TVShowLikeAdmin(admin.ModelAdmin):
    list_display = ['user', 'tvshow', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__email', 'tvshow__title']


@admin.register(EpisodeWatchHistory)
class EpisodeWatchHistoryAdmin(admin.ModelAdmin):
    list_display = ['user_profile', 'episode', 'watched_at', 'completed']
    list_filter = ['completed', 'watched_at']
    search_fields = ['user_profile__user__email', 'episode__title', 'episode__season__tvshow__title']
    raw_id_fields = ('user_profile', 'episode')
    date_hierarchy = 'watched_at'
