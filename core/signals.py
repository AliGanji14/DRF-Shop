from django.dispatch import receiver
from store.signals import order_created
import logging

logger = logging.getLogger(__name__)


@receiver(order_created)
def order_created_handler(sender, order, **kwargs):
    logger.info(
        "Order created",
        extra={"order_id": order.id},
    )
