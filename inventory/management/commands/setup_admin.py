from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from inventory.models import UserProfile

class Command(BaseCommand):
    help = 'Sets up an admin user with proper role'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username for the admin user')
        parser.add_argument('password', type=str, help='Password for the admin user')
        parser.add_argument('--email', type=str, help='Email for the admin user', default='')

    def handle(self, *args, **options):
        username = options['username']
        password = options['password']
        email = options['email']

        try:
            # Create or get the user
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'is_staff': True,
                    'is_superuser': True
                }
            )
            
            if created:
                user.set_password(password)
                user.save()
                self.stdout.write(self.style.SUCCESS(f'Created superuser "{username}"'))
            else:
                self.stdout.write(self.style.WARNING(f'User "{username}" already exists'))
                if input('Do you want to update the password? (y/n): ').lower() == 'y':
                    user.set_password(password)
                    user.save()
                    self.stdout.write(self.style.SUCCESS(f'Updated password for "{username}"'))

            # Set up the user profile with admin role
            profile, profile_created = UserProfile.objects.get_or_create(
                user=user,
                defaults={'role': 'admin'}
            )
            
            if not profile_created and profile.role != 'admin':
                profile.role = 'admin'
                profile.save()
                self.stdout.write(self.style.SUCCESS(f'Updated role to admin for "{username}"'))
            elif profile_created:
                self.stdout.write(self.style.SUCCESS(f'Created admin profile for "{username}"'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error setting up admin user: {str(e)}')) 