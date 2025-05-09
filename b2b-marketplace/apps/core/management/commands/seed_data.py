from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.contrib.auth import get_user_model
# Import models from your apps that you want to seed
# from apps.accounts.models import Profile
# from apps.listings.models import Category, Material, Design
# from apps.payments_monetization.models import SubscriptionPlan

User = get_user_model()

class Command(BaseCommand):
    help = 'Seeds the database with initial data for development or testing.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before seeding (use with caution!).',
        )
        # Add more arguments if needed, e.g., --users=10 to specify number of users to create

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting data seeding process...'))

        if options['clear']:
            self.stdout.write(self.style.WARNING('Clearing existing data...'))
            # Add logic to clear specific models if needed. Be very careful with this.
            # Example: Category.objects.all().delete()
            # User.objects.filter(is_superuser=False).delete() # Don't delete superuser
            self.stdout.write(self.style.WARNING('Data clearing placeholder. Implement carefully.'))


        self._create_users()
        self._create_subscription_plans()
        self._create_listing_categories()
        # Add calls to other seeding methods

        self.stdout.write(self.style.SUCCESS('Successfully seeded data.'))

    def _create_users(self):
        self.stdout.write('Creating sample users...')
        # Create a superuser if one doesn't exist
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@example.com', 'adminpass')
            self.stdout.write(self.style.SUCCESS('Superuser "admin" created with password "adminpass".'))

        # Create sample users
        users_data = [
            {'username': 'buyer1', 'email': 'buyer1@example.com', 'password': 'password123', 'user_type': 'buyer', 'first_name': 'Bob', 'last_name': 'Buyer'},
            {'username': 'seller1', 'email': 'seller1@example.com', 'password': 'password123', 'user_type': 'seller', 'first_name': 'Sally', 'last_name': 'Seller'},
            {'username': 'designer1', 'email': 'designer1@example.com', 'password': 'password123', 'user_type': 'designer', 'first_name': 'Dave', 'last_name': 'Designer'},
            {'username': 'manu1', 'email': 'manu1@example.com', 'password': 'password123', 'user_type': 'manufacturer', 'first_name': 'Manny', 'last_name': 'Festo'},
        ]

        for data in users_data:
            if not User.objects.filter(username=data['username']).exists():
                user = User.objects.create_user(
                    username=data['username'],
                    email=data['email'],
                    password=data['password'],
                    user_type=data['user_type'],
                    first_name=data.get('first_name', ''),
                    last_name=data.get('last_name', '')
                )
                # Profile is created via signal, but you can update it here
                # if hasattr(user, 'profile'):
                #     user.profile.company_name = f"{data['first_name']}'s Company"
                #     user.profile.save()
                self.stdout.write(f'User "{user.username}" created.')
            else:
                self.stdout.write(f'User "{data["username"]}" already exists.')


    def _create_subscription_plans(self):
        # from apps.payments_monetization.models import SubscriptionPlan # Local import
        # self.stdout.write('Creating subscription plans...')
        # plans_data = [
        #     {'name': 'Basic', 'price': 0.00, 'interval': 'month', 'features': {"listings_limit": 5}, 'stripe_plan_id': 'price_basic_000'},
        #     {'name': 'Pro', 'price': 29.99, 'interval': 'month', 'features': {"listings_limit": 50, "priority_support": True}, 'stripe_plan_id': 'price_pro_123'},
        #     {'name': 'Enterprise', 'price': 99.99, 'interval': 'month', 'features': {"listings_limit": "unlimited", "analytics_access": "full"}, 'stripe_plan_id': 'price_ent_456'},
        # ]
        # for data in plans_data:
        #     plan, created = SubscriptionPlan.objects.get_or_create(
        #         name=data['name'],
        #         defaults=data
        #     )
        #     if created:
        #         self.stdout.write(f'Subscription plan "{plan.name}" created.')
        #     else:
        #         self.stdout.write(f'Subscription plan "{plan.name}" already exists.')
        self.stdout.write(self.style.NOTICE('Subscription plan seeding placeholder.'))


    def _create_listing_categories(self):
        # from apps.listings.models import Category # Local import
        # self.stdout.write('Creating listing categories...')
        # categories = ['Fabrics', 'Trims', 'Accessories', 'Sustainable Materials', 'Tech Textiles']
        # for cat_name in categories:
        #     category, created = Category.objects.get_or_create(name=cat_name)
        #     if created:
        #         self.stdout.write(f'Category "{category.name}" created.')
        #     else:
        #         self.stdout.write(f'Category "{category.name}" already exists.')
        self.stdout.write(self.style.NOTICE('Listing category seeding placeholder.'))

    # Add more methods like _create_materials, _create_designs, etc.
    # Remember to use get_or_create to avoid duplicates if the command is run multiple times.