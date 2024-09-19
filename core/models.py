from django.db import models
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    email = models.EmailField(
        unique=True, max_length=254, verbose_name='email address')

