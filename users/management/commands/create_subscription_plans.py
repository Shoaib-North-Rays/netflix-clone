from django.core.management.base import BaseCommand
from users.models import SubscriptionPlan


class Command(BaseCommand):
    help = 'Create initial subscription plans'

    def handle(self, *args, **options):
        self.stdout.write('Creating subscription plans...')
        
        plans_data = [
            {
                'name': 'basic',
                'display_name': 'Basic',
                'price': 8.99,
                'duration_days': 30,
                'max_streams': 1,
                'hd_quality': False,
                'ultra_hd_quality': False,
                'download_allowed': True,
                'description': 'Good video quality (720p), watch on 1 device at a time, download on 1 device.',
                'is_active': True
            },
            {
                'name': 'standard',
                'display_name': 'Standard',
                'price': 13.99,
                'duration_days': 30,
                'max_streams': 2,
                'hd_quality': True,
                'ultra_hd_quality': False,
                'download_allowed': True,
                'description': 'Better video quality (1080p), watch on 2 devices at a time, download on 2 devices.',
                'is_active': True
            },
            {
                'name': 'premium',
                'display_name': 'Premium',
                'price': 17.99,
                'duration_days': 30,
                'max_streams': 4,
                'hd_quality': True,
                'ultra_hd_quality': True,
                'download_allowed': True,
                'description': 'Best video quality (4K+HDR), watch on 4 devices at a time, download on 6 devices.',
                'is_active': True
            }
        ]
        
        for plan_data in plans_data:
            plan, created = SubscriptionPlan.objects.get_or_create(
                name=plan_data['name'],
                defaults=plan_data
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Created plan: {plan.display_name} (${plan.price}/month)')
                )
            else:
                # Update existing plan
                for key, value in plan_data.items():
                    if key != 'name':  # Don't update the unique name field
                        setattr(plan, key, value)
                plan.save()
                self.stdout.write(
                    self.style.WARNING(f'⚠️  Updated existing plan: {plan.display_name} (${plan.price}/month)')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully processed {len(plans_data)} subscription plans!')
        )