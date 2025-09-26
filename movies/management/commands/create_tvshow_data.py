from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from movies.models import Genre, Actor, Director, TVShow, Season, Episode
from django.utils.text import slugify
from django.core.files.base import ContentFile
import requests
from io import BytesIO
from datetime import datetime, timedelta
import random

User = get_user_model()


class Command(BaseCommand):
    help = 'Create sample TV show data with episodes and images'

    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-images',
            action='store_true',
            help='Skip downloading images',
        )

    def handle(self, *args, **options):
        self.skip_images = options.get('skip_images', False)
        self.stdout.write('Creating TV show sample data...')
        
        # Get existing genres, actors, directors (or create if needed)
        genres = self.get_or_create_genres()
        actors = self.get_or_create_actors()
        directors = self.get_or_create_directors()
        
        # Create TV shows
        self.create_tvshows(genres, actors, directors)
        
        self.stdout.write(
            self.style.SUCCESS('Successfully created TV show sample data!')
        )

    def get_or_create_genres(self):
        """Get existing genres or create TV-specific ones"""
        genres_data = [
            {'name': 'Drama', 'description': 'Dramatic series with complex storylines'},
            {'name': 'Comedy', 'description': 'Comedy series and sitcoms'},
            {'name': 'Action', 'description': 'Action-packed series with thrills'},
            {'name': 'Sci-Fi', 'description': 'Science fiction and futuristic series'},
            {'name': 'Crime', 'description': 'Crime dramas and detective series'},
            {'name': 'Fantasy', 'description': 'Fantasy worlds and magical elements'},
            {'name': 'Horror', 'description': 'Horror and supernatural series'},
            {'name': 'Thriller', 'description': 'Suspenseful and tension-filled series'},
            {'name': 'Romance', 'description': 'Romantic storylines and relationships'},
            {'name': 'Documentary', 'description': 'Documentary and factual series'},
            {'name': 'Animation', 'description': 'Animated series for all ages'},
            {'name': 'Mystery', 'description': 'Mystery and detective series'},
        ]
        
        genres = []
        for genre_data in genres_data:
            genre, created = Genre.objects.get_or_create(
                name=genre_data['name'],
                defaults={
                    'slug': slugify(genre_data['name']),
                    'description': genre_data['description']
                }
            )
            genres.append(genre)
            if created:
                self.stdout.write(f'Created genre: {genre.name}')
        
        return genres

    def get_or_create_actors(self):
        """Get existing actors or create TV-specific ones"""
        tv_actors_data = [
            {'name': 'Bryan Cranston', 'nationality': 'American'},
            {'name': 'Emilia Clarke', 'nationality': 'British'},
            {'name': 'Kit Harington', 'nationality': 'British'},
            {'name': 'Peter Dinklage', 'nationality': 'American'},
            {'name': 'Claire Foy', 'nationality': 'British'},
            {'name': 'Millie Bobby Brown', 'nationality': 'British'},
            {'name': 'Finn Wolfhard', 'nationality': 'Canadian'},
            {'name': 'David Harbour', 'nationality': 'American'},
            {'name': 'Winona Ryder', 'nationality': 'American'},
            {'name': 'Pedro Pascal', 'nationality': 'Chilean'},
            {'name': 'Bella Ramsey', 'nationality': 'British'},
            {'name': 'Anna Torv', 'nationality': 'Australian'},
            {'name': 'Oscar Isaac', 'nationality': 'American'},
            {'name': 'Jessica Chastain', 'nationality': 'American'},
            {'name': 'Jason Bateman', 'nationality': 'American'},
            {'name': 'Julia Garner', 'nationality': 'American'},
            {'name': 'Laura Linney', 'nationality': 'American'},
            {'name': 'Henry Cavill', 'nationality': 'British'},
            {'name': 'Anya Chalotra', 'nationality': 'British'},
            {'name': 'Freya Allan', 'nationality': 'British'},
        ]
        
        actors = []
        for actor_data in tv_actors_data:
            actor, created = Actor.objects.get_or_create(
                name=actor_data['name'],
                defaults={'nationality': actor_data['nationality']}
            )
            actors.append(actor)
            if created:
                self.stdout.write(f'Created actor: {actor.name}')
        
        return actors

    def get_or_create_directors(self):
        """Get existing directors or create TV-specific ones"""
        tv_directors_data = [
            {'name': 'Vince Gilligan', 'nationality': 'American'},
            {'name': 'David Benioff', 'nationality': 'American'},
            {'name': 'D.B. Weiss', 'nationality': 'American'},
            {'name': 'The Duffer Brothers', 'nationality': 'American'},
            {'name': 'Peter Morgan', 'nationality': 'British'},
            {'name': 'Lauren Schmidt Hissrich', 'nationality': 'American'},
            {'name': 'Craig Mazin', 'nationality': 'American'},
            {'name': 'Neil Druckmann', 'nationality': 'Israeli-American'},
            {'name': 'Chris Mundy', 'nationality': 'American'},
            {'name': 'Ryan J. Condal', 'nationality': 'American'},
        ]
        
        directors = []
        for director_data in tv_directors_data:
            director, created = Director.objects.get_or_create(
                name=director_data['name'],
                defaults={'nationality': director_data['nationality']}
            )
            directors.append(director)
            if created:
                self.stdout.write(f'Created director: {director.name}')
        
        return directors

    def download_image(self, url, filename):
        """Download image from URL and return ContentFile"""
        if self.skip_images:
            return None
            
        try:
            self.stdout.write(f'Downloading {filename} from {url}')
            response = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
            if response.status_code == 200:
                self.stdout.write(f'Successfully downloaded {filename}')
                return ContentFile(response.content, filename)
            else:
                self.stdout.write(f'Failed to download {filename}: HTTP {response.status_code}')
        except Exception as e:
            self.stdout.write(f'Failed to download image {filename}: {e}')
        return None

    def create_tvshows(self, genres, actors, directors):
        """Create sample TV shows with seasons and episodes"""
        tvshows_data = [
            {
                'title': 'Breaking Bad',
                'description': 'A high school chemistry teacher turned methamphetamine producer partners with a former student to secure his family\'s financial future.',
                'first_air_date': datetime(2008, 1, 20).date(),
                'last_air_date': datetime(2013, 9, 29).date(),
                'status': 'ended',
                'rating': 'TV-MA',
                'imdb_rating': 9.5,
                'is_featured': True,
                'is_trending': True,
                'total_seasons': 5,
                'genres': ['Drama', 'Crime', 'Thriller'],
                'actors': ['Bryan Cranston'],
                'directors': ['Vince Gilligan'],
                'thumbnail_url': 'https://picsum.photos/300/450?random=1',
                'banner_url': 'https://picsum.photos/1920/1080?random=1',
                'trailer_url': 'https://www.youtube.com/watch?v=HhesaQXLuRY',
                'seasons_data': [
                    {
                        'season_number': 1,
                        'title': 'Season 1',
                        'description': 'Walter White begins his transformation.',
                        'episodes': [
                            {'title': 'Pilot', 'description': 'Walter White discovers he has cancer and starts cooking meth.', 'duration': 58},
                            {'title': 'Cat\'s in the Bag...', 'description': 'Walter and Jesse dispose of evidence.', 'duration': 48},
                            {'title': '...And the Bag\'s in the River', 'description': 'Walter makes a difficult decision.', 'duration': 48},
                            {'title': 'Cancer Man', 'description': 'Walter tells his family about his cancer.', 'duration': 48},
                            {'title': 'Gray Matter', 'description': 'Walter rejects help from old friends.', 'duration': 48},
                        ]
                    },
                    {
                        'season_number': 2,
                        'title': 'Season 2',
                        'description': 'The consequences of Walter\'s actions begin to unfold.',
                        'episodes': [
                            {'title': 'Seven Thirty-Seven', 'description': 'Walter and Jesse face new challenges.', 'duration': 47},
                            {'title': 'Grilled', 'description': 'A dangerous encounter with Tuco.', 'duration': 47},
                            {'title': 'Bit by a Dead Bee', 'description': 'Walter and Jesse try to cover their tracks.', 'duration': 47},
                        ]
                    }
                ]
            },
            {
                'title': 'Stranger Things',
                'description': 'In 1980s Indiana, a group of young friends witness supernatural forces and secret government exploits.',
                'first_air_date': datetime(2016, 7, 15).date(),
                'status': 'ongoing',
                'rating': 'TV-14',
                'imdb_rating': 8.7,
                'is_featured': True,
                'is_trending': True,
                'total_seasons': 4,
                'genres': ['Sci-Fi', 'Horror', 'Drama'],
                'actors': ['Millie Bobby Brown', 'Finn Wolfhard', 'David Harbour', 'Winona Ryder'],
                'directors': ['The Duffer Brothers'],
                'thumbnail_url': 'https://picsum.photos/300/450?random=2',
                'banner_url': 'https://picsum.photos/1920/1080?random=2',
                'trailer_url': 'https://www.youtube.com/watch?v=b9EkMc79ZSU',
                'seasons_data': [
                    {
                        'season_number': 1,
                        'title': 'Season 1',
                        'description': 'Will Byers disappears and strange things start happening.',
                        'episodes': [
                            {'title': 'Chapter One: The Vanishing of Will Byers', 'description': 'Will disappears on his way home.', 'duration': 47},
                            {'title': 'Chapter Two: The Weirdo on Maple Street', 'description': 'Eleven appears and helps the boys.', 'duration': 55},
                            {'title': 'Chapter Three: Holly, Jolly', 'description': 'Joyce and Hopper investigate.', 'duration': 51},
                            {'title': 'Chapter Four: The Body', 'description': 'Will\'s body is found.', 'duration': 50},
                        ]
                    }
                ]
            },
            {
                'title': 'The Crown',
                'description': 'The political rivalries and romance of Queen Elizabeth II\'s reign and the events that shaped the second half of the 20th century.',
                'first_air_date': datetime(2016, 11, 4).date(),
                'status': 'ended',
                'rating': 'TV-MA',
                'imdb_rating': 8.7,
                'is_featured': True,
                'total_seasons': 6,
                'genres': ['Drama', 'Romance'],
                'actors': ['Claire Foy'],
                'directors': ['Peter Morgan'],
                'thumbnail_url': 'https://picsum.photos/300/450?random=3',
                'banner_url': 'https://picsum.photos/1920/1080?random=3',
                'seasons_data': [
                    {
                        'season_number': 1,
                        'title': 'Season 1',
                        'description': 'Elizabeth ascends to the throne.',
                        'episodes': [
                            {'title': 'Wolferton Splash', 'description': 'Elizabeth becomes queen.', 'duration': 57},
                            {'title': 'Hyde Park Corner', 'description': 'The royal family adapts to change.', 'duration': 56},
                            {'title': 'Windsor', 'description': 'Philip and Elizabeth face marital challenges.', 'duration': 56},
                        ]
                    }
                ]
            },
            {
                'title': 'The Last of Us',
                'description': 'Twenty years after a fungal outbreak ravages humanity, survivors Joel and Ellie navigate a post-apocalyptic America.',
                'first_air_date': datetime(2023, 1, 15).date(),
                'status': 'ongoing',
                'rating': 'TV-MA',
                'imdb_rating': 8.8,
                'is_trending': True,
                'total_seasons': 1,
                'genres': ['Drama', 'Horror', 'Thriller'],
                'actors': ['Pedro Pascal', 'Bella Ramsey', 'Anna Torv'],
                'directors': ['Craig Mazin', 'Neil Druckmann'],
                'thumbnail_url': 'https://picsum.photos/300/450?random=4',
                'banner_url': 'https://picsum.photos/1920/1080?random=4',
                'seasons_data': [
                    {
                        'season_number': 1,
                        'title': 'Season 1',
                        'description': 'Joel and Ellie\'s journey begins.',
                        'episodes': [
                            {'title': 'When You\'re Lost in the Darkness', 'description': 'The outbreak begins and Joel loses Sarah.', 'duration': 81},
                            {'title': 'Infected', 'description': 'Joel and Ellie encounter infected.', 'duration': 54},
                            {'title': 'Long, Long Time', 'description': 'Bill and Frank\'s story.', 'duration': 76},
                        ]
                    }
                ]
            },
            {
                'title': 'Ozark',
                'description': 'A financial advisor drags his family to Missouri to launder money for a Mexican cartel.',
                'first_air_date': datetime(2017, 7, 21).date(),
                'last_air_date': datetime(2022, 4, 29).date(),
                'status': 'ended',
                'rating': 'TV-MA',
                'imdb_rating': 8.4,
                'is_trending': True,
                'total_seasons': 4,
                'genres': ['Drama', 'Crime', 'Thriller'],
                'actors': ['Jason Bateman', 'Julia Garner', 'Laura Linney'],
                'directors': ['Chris Mundy'],
                'thumbnail_url': 'https://picsum.photos/300/450?random=5',
                'banner_url': 'https://picsum.photos/1920/1080?random=5',
                'seasons_data': [
                    {
                        'season_number': 1,
                        'title': 'Season 1',
                        'description': 'The Byrde family moves to the Ozarks.',
                        'episodes': [
                            {'title': 'Sugarwood', 'description': 'Marty Byrde must launder money in the Ozarks.', 'duration': 60},
                            {'title': 'Blue Cat', 'description': 'The Byrdes look for a business to buy.', 'duration': 51},
                            {'title': 'My Dripping Sleep', 'description': 'Marty finds a way to control Ruth.', 'duration': 58},
                        ]
                    }
                ]
            },
            {
                'title': 'The Witcher',
                'description': 'Geralt of Rivia, a monster hunter, struggles to find his place in a world where people are often more wicked than beasts.',
                'first_air_date': datetime(2019, 12, 20).date(),
                'status': 'ongoing',
                'rating': 'TV-MA',
                'imdb_rating': 8.2,
                'is_featured': True,
                'total_seasons': 3,
                'genres': ['Fantasy', 'Action', 'Adventure'],
                'actors': ['Henry Cavill', 'Anya Chalotra', 'Freya Allan'],
                'directors': ['Lauren Schmidt Hissrich'],
                'thumbnail_url': 'https://picsum.photos/300/450?random=6',
                'banner_url': 'https://picsum.photos/1920/1080?random=6',
                'seasons_data': [
                    {
                        'season_number': 1,
                        'title': 'Season 1',
                        'description': 'Geralt meets his destiny.',
                        'episodes': [
                            {'title': 'The End\'s Beginning', 'description': 'Geralt fights a kikimore and meets Renfri.', 'duration': 60},
                            {'title': 'Four Marks', 'description': 'Yennefer transforms at Aretuza.', 'duration': 60},
                            {'title': 'Betrayer Moon', 'description': 'Geralt is hired to lift a curse.', 'duration': 58},
                        ]
                    }
                ]
            },
            {
                'title': 'House of the Dragon',
                'description': 'The Targaryen dynasty at the height of its power, with more than 15 dragons under their yoke.',
                'first_air_date': datetime(2022, 8, 21).date(),
                'status': 'ongoing',
                'rating': 'TV-MA',
                'imdb_rating': 8.5,
                'is_trending': True,
                'total_seasons': 2,
                'genres': ['Fantasy', 'Drama', 'Action'],
                'actors': ['Emilia Clarke', 'Kit Harington', 'Peter Dinklage'],
                'directors': ['Ryan J. Condal'],
                'thumbnail_url': 'https://picsum.photos/300/450?random=7',
                'banner_url': 'https://picsum.photos/1920/1080?random=7',
                'seasons_data': [
                    {
                        'season_number': 1,
                        'title': 'Season 1',
                        'description': 'The Dance of Dragons begins.',
                        'episodes': [
                            {'title': 'The Heirs of the Dragon', 'description': 'King Viserys must choose an heir.', 'duration': 66},
                            {'title': 'The Rogue Prince', 'description': 'Daemon causes trouble in King\'s Landing.', 'duration': 54},
                            {'title': 'Second of His Name', 'description': 'Rhaenyra faces pressure to marry.', 'duration': 63},
                        ]
                    }
                ]
            },
            {
                'title': 'Wednesday',
                'description': 'Wednesday Addams navigates her years as a student at Nevermore Academy while solving a mystery.',
                'first_air_date': datetime(2022, 11, 23).date(),
                'status': 'ongoing',
                'rating': 'TV-14',
                'imdb_rating': 8.1,
                'is_trending': True,
                'total_seasons': 1,
                'genres': ['Comedy', 'Horror', 'Mystery'],
                'actors': ['Millie Bobby Brown'],  # Using existing actor
                'directors': ['The Duffer Brothers'],  # Using existing director
                'thumbnail_url': 'https://picsum.photos/300/450?random=8',
                'banner_url': 'https://picsum.photos/1920/1080?random=8',
                'seasons_data': [
                    {
                        'season_number': 1,
                        'title': 'Season 1',
                        'description': 'Wednesday starts at Nevermore Academy.',
                        'episodes': [
                            {'title': 'Wednesday\'s Child Is Full of Woe', 'description': 'Wednesday arrives at Nevermore Academy.', 'duration': 51},
                            {'title': 'Woe Is the Loneliest Number', 'description': 'Wednesday investigates a local murder.', 'duration': 47},
                            {'title': 'Friend or Woe', 'description': 'Wednesday joins the Poe Cup race.', 'duration': 52},
                        ]
                    }
                ]
            }
        ]
        
        for tvshow_data in tvshows_data:
            # Create TV Show
            tvshow, created = TVShow.objects.get_or_create(
                title=tvshow_data['title'],
                defaults={
                    'slug': slugify(tvshow_data['title']),
                    'description': tvshow_data['description'],
                    'first_air_date': tvshow_data['first_air_date'],
                    'last_air_date': tvshow_data.get('last_air_date'),
                    'status': tvshow_data['status'],
                    'rating': tvshow_data['rating'],
                    'imdb_rating': tvshow_data.get('imdb_rating'),
                    'is_featured': tvshow_data.get('is_featured', False),
                    'is_trending': tvshow_data.get('is_trending', False),
                    'trailer_url': tvshow_data.get('trailer_url', ''),
                }
            )
            
            if created:
                # Download and set images
                if 'thumbnail_url' in tvshow_data:
                    thumbnail_file = self.download_image(
                        tvshow_data['thumbnail_url'], 
                        f"{tvshow.slug}_thumbnail.jpg"
                    )
                    if thumbnail_file:
                        tvshow.thumbnail.save(
                            f"{tvshow.slug}_thumbnail.jpg", 
                            thumbnail_file, 
                            save=False
                        )
                
                if 'banner_url' in tvshow_data:
                    banner_file = self.download_image(
                        tvshow_data['banner_url'], 
                        f"{tvshow.slug}_banner.jpg"
                    )
                    if banner_file:
                        tvshow.banner_image.save(
                            f"{tvshow.slug}_banner.jpg", 
                            banner_file, 
                            save=False
                        )
                
                tvshow.save()
                
                # Add genres
                tvshow_genres = Genre.objects.filter(name__in=tvshow_data['genres'])
                tvshow.genres.set(tvshow_genres)
                
                # Add actors
                tvshow_actors = Actor.objects.filter(name__in=tvshow_data['actors'])
                tvshow.actors.set(tvshow_actors)
                
                # Add directors
                tvshow_directors = Director.objects.filter(name__in=tvshow_data['directors'])
                tvshow.directors.set(tvshow_directors)
                
                self.stdout.write(f'Created TV show: {tvshow.title}')
                
                # Create seasons and episodes
                self.create_seasons_and_episodes(tvshow, tvshow_data.get('seasons_data', []))
    
    def create_seasons_and_episodes(self, tvshow, seasons_data):
        """Create seasons and episodes for a TV show"""
        for season_data in seasons_data:
            season, created = Season.objects.get_or_create(
                tvshow=tvshow,
                season_number=season_data['season_number'],
                defaults={
                    'title': season_data.get('title', f"Season {season_data['season_number']}"),
                    'description': season_data.get('description', ''),
                    'air_date': tvshow.first_air_date + timedelta(days=365 * (season_data['season_number'] - 1)),
                }
            )
            
            if created:
                self.stdout.write(f'  Created season: {season.title} for {tvshow.title}')
                
                # Create episodes
                for i, episode_data in enumerate(season_data.get('episodes', []), 1):
                    episode, ep_created = Episode.objects.get_or_create(
                        season=season,
                        episode_number=i,
                        defaults={
                            'title': episode_data['title'],
                            'description': episode_data['description'],
                            'duration': episode_data.get('duration', 45),
                            'air_date': season.air_date + timedelta(days=7 * (i - 1)),  # Weekly episodes
                        }
                    )
                    
                    if ep_created:
                        # Download episode thumbnail
                        episode_thumbnail_url = f"https://picsum.photos/640/360?random={tvshow.id}{season.season_number}{i}"
                        thumbnail_file = self.download_image(
                            episode_thumbnail_url,
                            f"{tvshow.slug}_s{season.season_number}e{i}_thumbnail.jpg"
                        )
                        if thumbnail_file:
                            episode.thumbnail.save(
                                f"{tvshow.slug}_s{season.season_number}e{i}_thumbnail.jpg",
                                thumbnail_file,
                                save=False
                            )
                            episode.save()
                        
                        self.stdout.write(f'    Created episode: S{season.season_number}E{i} - {episode.title}')
                
                # Note: episode_count is a property, no need to save it
        
        # Note: total_episodes is a property, calculated automatically
