from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from attendance.models import Profile

class Command(BaseCommand):
    help = 'Create missing Profile objects for all users.'

    def handle(self, *args, **options):
        created_count = 0
        for user in User.objects.all():
            profile, created = Profile.objects.get_or_create(user=user)
            if created:
                created_count += 1
        self.stdout.write(self.style.SUCCESS(f'Created {created_count} missing profiles.')) 