from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import BankDetailsAck, BankDetails


@receiver(post_save, sender=BankDetailsAck)
def update_payee_acknowledgement(sender, instance, created, **kwargs):
    if created and instance.is_approved:
        payee = instance.payee
        try:
            bank_details = BankDetails.objects.get(payee=payee)
            bank_details.payee_acknowledgement = True
            bank_details.save(update_fields=['payee_acknowledgement'])
        except BankDetails.DoesNotExist:
            pass
