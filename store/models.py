from django.db import models
from django.conf import settings
import uuid
from django.core.validators import RegexValidator, MinValueValidator

phone_validator = RegexValidator(
    regex=r"^\+?1?\d{9,15}$",
    message="Phone number must be entered in the format: '+989123456789'.",
)


class TimeStampedModel(models.Model):
    datetime_created = models.DateTimeField(auto_now_add=True)
    datetime_modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Category(models.Model):
    title = models.CharField(max_length=255)
    description = models.CharField(max_length=500, blank=True)
    top_product = models.ForeignKey(
        "Product", on_delete=models.SET_NULL, null=True, related_name="+"
    )

    class Meta:
        verbose_name = "category"
        verbose_name_plural = "categories"
        ordering = ["title"]

    def __str__(self):
        return self.title


class Discount(models.Model):
    discount = models.DecimalField(max_digits=5, decimal_places=2)
    description = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.discount} | {self.description}"


class Product(TimeStampedModel):
    name = models.CharField(max_length=255)
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name="products"
    )
    slug = models.SlugField(unique=True)
    description = models.TextField()
    unit_price = models.DecimalField(max_digits=6, decimal_places=2)
    inventory = models.IntegerField(validators=[MinValueValidator(0)])
    discounts = models.ManyToManyField(Discount, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Customer(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    phone_number = models.CharField(max_length=20, validators=[phone_validator])
    birth_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"

    class Meta:
        permissions = [
            ("send_private_email", "Can send private email to user bye the button")
        ]


class Address(models.Model):
    customer = models.OneToOneField(
        Customer, on_delete=models.CASCADE, primary_key=True
    )
    province = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    street = models.CharField(max_length=255)

    def __str__(self):
        return f"Comment by {self.name}"


class UnpaidOrderManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(status=Order.ORDER_STATUS_UNPAID)


class OrderStatus(models.TextChoices):
    PAID = "p", "Paid"
    UNPAID = "u", "Unpaid"
    CANCELED = "c", "Canceled"


class Order(TimeStampedModel):
    customer = models.ForeignKey(
        Customer, on_delete=models.PROTECT, related_name="orders"
    )
    status = models.CharField(
        max_length=1, choices=OrderStatus.choices, default=OrderStatus.UNPAID
    )

    class Meta:
        ordering = ["-datetime_created"]

    objects = models.Manager()
    unpaid_orders = UnpaidOrderManager()

    def __str__(self):
        return f"order id: {self.id}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name="items")
    product = models.ForeignKey(
        Product, on_delete=models.PROTECT, related_name="order_items"
    )
    quantity = models.PositiveSmallIntegerField()
    unit_price = models.DecimalField(max_digits=6, decimal_places=2)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["order", "product"], name="unique_order_product"
            )
        ]

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"


class CommentManager(models.Manager):
    def get_approved(self):
        return self.get_queryset().filter(status=Comment.COMMENT_STATUS_APPROVED)


class ApprovedCommentManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(status=Comment.COMMENT_STATUS_APPROVED)


class CommentStatus(models.TextChoices):
    WAITING = "w", "Waiting"
    APPROVED = "a", "Approved"
    NOT_APPROVED = "na", "Not Approved"


class Comment(TimeStampedModel):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="comments"
    )
    name = models.CharField(max_length=255)
    body = models.TextField()
    status = models.CharField(
        max_length=2, choices=CommentStatus.choices, default=CommentStatus.WAITING
    )

    class Meta:
        ordering = ["-datetime_created"]

    objects = CommentManager()
    approved = ApprovedCommentManager()


class Cart(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    def __str__(self):
        return f"Cart {self.id}"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="cart_items"
    )
    quantity = models.PositiveSmallIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["cart", "product"], name="unique_cart_product"
            )
        ]

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"
