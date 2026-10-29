from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.contrib.auth.models import User
from core.models import UserProfile, Product, Order


class Command(BaseCommand):
    help = "Loads all original FarmConnect data (Users, Farmer Profiles, Harvests, and Orders) into the database."

    def handle(self, *args, **options):
        self.stdout.write("Loading seed_data fixture into database...")
        try:
            call_command('loaddata', 'seed_data', verbosity=1)
            self.stdout.write(self.style.SUCCESS(
                f"Successfully loaded data!\n"
                f"  - Users: {User.objects.count()}\n"
                f"  - UserProfiles: {UserProfile.objects.count()}\n"
                f"  - Products: {Product.objects.count()}\n"
                f"  - Orders: {Order.objects.count()}"
            ))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Failed to load seed_data: {e}"))
