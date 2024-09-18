from django.contrib import admin

from .models import Comment, Customer, Cart

admin.site.register(Comment)
admin.site.register(Customer)
admin.site.register(Cart)
