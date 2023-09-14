from django.contrib import admin
from .models import Category, MenuItem, Cart, Order, OrderItem

# Register your models here.
admin.site.register([Category, MenuItem])
admin.site.register([Cart, Order])
admin.site.register(OrderItem)