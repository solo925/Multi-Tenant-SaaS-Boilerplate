from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Payment
from django.core.mail import send_mail

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
