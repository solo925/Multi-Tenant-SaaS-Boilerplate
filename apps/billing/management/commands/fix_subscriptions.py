from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.billing.models import Plan, Subscription
from datetime import date, timedelta

User = get_user_model()

class Command(BaseCommand):
    help = 'Create free trial subscriptions for users who don\'t have active subscriptions'

    def handle(self, *args, **options):
        # Get or create a free trial plan
        free_plan, created = Plan.objects.get_or_create(
            name="Free Trial",
            defaults={
                'description': '30-day free trial with full access',
                'price': 0.00,
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS('Created Free Trial plan')
            )

        # Find users without active subscriptions
        users_without_subs = []
        for user in User.objects.all():
            active_sub = Subscription.objects.filter(
                user=user, 
                active=True,
                end_date__gte=date.today()
            ).first()
            
            if not active_sub:
                users_without_subs.append(user)

        # Create subscriptions for users without them
        created_count = 0
        for user in users_without_subs:
            Subscription.objects.create(
                user=user,
                plan=free_plan,
                start_date=date.today(),
                end_date=date.today() + timedelta(days=30),
                active=True
            )
            created_count += 1
            self.stdout.write(f'Created subscription for {user.email}')

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {created_count} free trial subscriptions'
            )
        )
