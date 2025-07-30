from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Payment, Subscription, Plan
from django.core.mail import send_mail
from django.conf import settings
from datetime import date, timedelta

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_free_trial_subscription(sender, instance, created, **kwargs):
    """Automatically create a 30-day free trial subscription for new users."""
    if created:
        # Get or create a free trial plan
        free_plan, _ = Plan.objects.get_or_create(
            name="Free Trial",
            defaults={
                'description': '30-day free trial with full access',
                'price': 0.00,
                'is_active': True
            }
        )
        
        # Create subscription for the new user
        Subscription.objects.create(
            user=instance,
            plan=free_plan,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            active=True
        )


@receiver(post_save, sender=Payment)
def send_payment_receipt(sender, instance, created, **kwargs):
    if created:
        send_mail(
            subject="Your Payment Receipt",
            message=f"Thank you! You paid ${instance.amount} on {instance.date.strftime('%Y-%m-%d')}.",
            from_email="billing@yourapp.com",
            recipient_list=[instance.user.email],
            fail_silently=True,
        )
