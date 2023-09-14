from rest_framework import serializers, permissions
from django.contrib.auth.models import User 
from .models import Category, MenuItem, Cart, Order, OrderItem
from rest_framework.validators import UniqueTogetherValidator
from rest_framework.permissions import BasePermission
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from .perms import isManager, isDeliveryCrew, isCustomer

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'email', 'id')

class CategorySerializer (serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['slug','title']

class MenuItemSerializer(serializers.ModelSerializer):
    #category_id = serializers.IntegerField(write_only=True)
    #queryset=Category.objects.all()
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())
    class Meta:
        model = MenuItem
        fields = ['id','title','price','featured','category']
        validators = [
    UniqueTogetherValidator(
        queryset=MenuItem.objects.all(),
        fields=['title']
    )]
        
class CartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cart
        fields = ['user','menuitem','quantity','unit_price', 'price']

class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model=Order
        fields= ['user', 'delivery_crew', 'status', 'total', 'date']

class OrderItemsSerializer(serializers.ModelSerializer):

    class Meta:
        model=OrderItem
        fields=['order', 'menuitem', 'quantity','unit_price', 'price']
    