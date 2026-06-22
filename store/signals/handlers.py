from django.db.models.signals import post_save,post_delete
from django.dispatch import receiver
from django.conf import settings
from django.core.cache import cache

from store.models import Customer


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_customer_profile_for_newly_created_user(sender, instance, created, **kwargs):
    if created:
        Customer.objects.create(user=instance)


@receiver(post_save)
def clear_cache_on_save(sender, instance, **kwargs):
    try:
        if sender.__module__.startswith('store.') or getattr(sender._meta, 'app_label', '') == 'store':
            cache.clear()
    except Exception:
        # avoid raising during migrations or other operations
        pass


@receiver(post_delete)
def clear_cache_on_delete(sender, instance, **kwargs):
    try:
        if sender.__module__.startswith('store.') or getattr(sender._meta, 'app_label', '') == 'store':
            cache.clear()
    except Exception:
        pass