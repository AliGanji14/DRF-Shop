from django.contrib import admin

from .models import Comment, Customer

admin.site.register(Comment)
admin.site.register(Customer)
