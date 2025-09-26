from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from movies.models import Movie
import requests
from io import BytesIO
from PIL import Image
import os


class Command(BaseCommand):
    help = 'Add dummy placeholder images for movies'

    def handle(self, *args, **options):
        self.stdout.write('Adding dummy images for movies...')
        
        # Movie poster dimensions (Netflix style)
        poster_width = 300
        poster_height = 450
        banner_width = 1920
        banner_height = 1080
        
        movies = Movie.objects.all()
        
        for movie in movies:
            self.stdout.write(f'Processing {movie.title}...')
            
            try:
                # Create thumbnail if not exists
                if not movie.thumbnail:
                    thumbnail_image = self.create_placeholder_image(
                        poster_width, 
                        poster_height, 
                        movie.title,
                        '#1a1a1a'  # Dark background
                    )
                    movie.thumbnail.save(
                        f'{movie.slug}-poster.jpg',
                        thumbnail_image,
                        save=False
                    )
                
                # Create banner if not exists
                if not movie.banner_image:
                    banner_image = self.create_placeholder_image(
                        banner_width, 
                        banner_height, 
                        movie.title,
                        '#2a2a2a'  # Slightly lighter for banner
                    )
                    movie.banner_image.save(
                        f'{movie.slug}-banner.jpg',
                        banner_image,
                        save=False
                    )
                
                movie.save()
                self.stdout.write(f'✅ Added images for {movie.title}')
                
            except Exception as e:
                self.stdout.write(f'❌ Error processing {movie.title}: {str(e)}')
        
        self.stdout.write(
            self.style.SUCCESS('Successfully added dummy images for all movies!')
        )

    def create_placeholder_image(self, width, height, text, bg_color):
        """Create a placeholder image with movie title"""
        from PIL import Image, ImageDraw, ImageFont
        
        # Create image
        image = Image.new('RGB', (width, height), bg_color)
        draw = ImageDraw.Draw(image)
        
        # Try to use a system font, fallback to default
        try:
            # Try different font sizes based on image size
            font_size = int(height * 0.08) if height > 500 else int(height * 0.12)
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            try:
                font_size = int(height * 0.08) if height > 500 else int(height * 0.12)
                font = ImageFont.truetype("calibri.ttf", font_size)
            except:
                # Use default font if no system fonts available
                font = ImageFont.load_default()
        
        # Text wrapping for long titles
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            text_width = bbox[2] - bbox[0]
            
            if text_width <= width * 0.8:  # 80% of image width
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    lines.append(word)
        
        if current_line:
            lines.append(' '.join(current_line))
        
        # Calculate total text height
        total_height = 0
        line_heights = []
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            line_height = bbox[3] - bbox[1]
            line_heights.append(line_height)
            total_height += line_height
        
        # Add spacing between lines
        line_spacing = font_size // 4
        total_height += line_spacing * (len(lines) - 1)
        
        # Start drawing from center
        y_start = (height - total_height) // 2
        
        for i, line in enumerate(lines):
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x = (width - text_width) // 2
            y = y_start + sum(line_heights[:i]) + (line_spacing * i)
            
            draw.text((x, y), line, fill='white', font=font)
        
        # Add decorative elements
        # Draw border
        border_width = 3
        draw.rectangle([0, 0, width-1, height-1], outline='#E50914', width=border_width)
        
        # Add gradient effect (simulate with rectangles)
        overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        
        # Bottom gradient
        for i in range(height//3):
            alpha = int((i / (height//3)) * 100)
            overlay_draw.rectangle(
                [0, height - height//3 + i, width, height - height//3 + i + 1], 
                fill=(0, 0, 0, alpha)
            )
        
        # Composite the overlay
        image = Image.alpha_composite(image.convert('RGBA'), overlay).convert('RGB')
        
        # Save to BytesIO
        image_io = BytesIO()
        image.save(image_io, format='JPEG', quality=85)
        image_io.seek(0)
        
        return ContentFile(image_io.getvalue())