from rest_framework import serializers, permissions
from django.contrib.auth.models import User, Group
from .models import Category, MenuItem, Cart, Order, OrderItem
from rest_framework.validators import UniqueTogetherValidator, UniqueValidator
from rest_framework.permissions import BasePermission
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from .perms import IsManager, IsDeliveryCrew, IsCustomer
from django.db import transaction
import random
import string


class UserSerializer(serializers.ModelSerializer):
    # id = serializers.ReadOnlyField()
    # group = serializers.CharField(write_only=True)
    

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username', 'email','password', 'id')
        extra_kwargs = {
            'username': {
                'validators': [UniqueValidator(queryset=User.objects.all())],
            },
            'email': {
                'validators': [UniqueValidator(queryset=User.objects.all())],
            },
        }

    def create(self, validated_data):
        group_name = validated_data.pop('group', None)  # Remove 'group' from validated_data
        user = User.objects.create(**validated_data)
        
        if group_name:
            try:
                group = Group.objects.get(name=group_name)
                user.groups.add(group)
                return {'detail': f"User '{user.username}' has been added to group '{group.name}'."}
            except Group.DoesNotExist:
                return {'detail': f"Group '{group_name}' does not exist."}
        
        return user

class CustomerSignUpSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username', 'email', 'password' ,'id')
        extra_kwargs = {
            'username': {
                'validators': [UniqueValidator(queryset=User.objects.all())],
            },
            'email': {
                'validators': [UniqueValidator(queryset=User.objects.all())],
            },
        }

class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ('name',)
    
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


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
    unit_price = serializers.ReadOnlyField()
    price = serializers.ReadOnlyField()
    user = serializers.ReadOnlyField(source='user.username')
    #cart_id = serializers.CharField(write_only=True)  # Change to CharField

    class Meta:
        model = Cart
        fields = ['user', 'menuitem', 'quantity', 'unit_price', 'price']

    def create(self, validated_data):
        menuitem = validated_data['menuitem']
        quantity = validated_data['quantity']
        user = self.context['request'].user  # Get the currently authenticated user

        unit_price = menuitem.price  # Assuming 'price' is a field on the MenuItem model
        price = unit_price * quantity

        # Generate a unique cart_id
        #def generate_cart_id(length=5):
        # Generate a random string of alphanumeric characters
        #    cart_id = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))
        #    return cart_id
        
        #cart_id = generate_cart_id()

        # Try to get an existing cart entry for the same user and menu item
        cart, created = Cart.objects.get_or_create(
            user=user,
            menuitem=menuitem,
            defaults={
                'quantity': quantity,
                'unit_price': unit_price,
                'price': price,
                #'cart_id': cart_id,  # Include the generated cart_id
            }
        )

        # If an existing entry was found, update its quantity
        if not created:
            cart.quantity += quantity
            cart.price += price
            cart.save()

        return cart

class OrderSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')
    date = serializers.ReadOnlyField(source='order.date')

    # Add a field for assigning delivery crew
    assigned_delivery_crew = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Order
        fields = ['user', 'delivery_crew', 'status', 'total', 'date', 'assigned_delivery_crew']

    def create(self, validated_data):
        # Get the current user
        user = self.context['request'].user

        # Calculate the total based on the user's cart items
        cart_items = Cart.objects.filter(user=user)
        total = sum(cart_item.price for cart_item in cart_items)

        # Get the assigned_delivery_crew from the validated data
        assigned_delivery_crew = validated_data.pop('assigned_delivery_crew', None)

        # Create the order
        order = Order.objects.create(
            user=user,
            delivery_crew=None,  # You can set this based on your logic
            status=validated_data.get('status', False),  # Adjust this based on your requirements
            total=total,
            date=validated_data.get('date', None),  # Adjust this based on your requirements
        )

        # Optionally, you can associate cart items with this order, e.g., mark them as ordered

        # Assign the delivery crew if provided
        if assigned_delivery_crew:
            order.delivery_crew = assigned_delivery_crew
            order.save()

        # Clear the user's cart after creating the order
        cart_items.delete()

        return order

class OrderItemsSerializer(serializers.ModelSerializer):
    order_number = serializers.CharField(write_only=True, required=True)

    # Other fields sourced from Cart
    menuitem = serializers.PrimaryKeyRelatedField(queryset=MenuItem.objects.all(), write_only=True)
    quantity = serializers.ReadOnlyField(source='cart.quantity')
    unit_price = serializers.ReadOnlyField(source='cart.unit_price')
    price = serializers.ReadOnlyField(source='cart.price')

    class Meta:
        model = OrderItem
        fields = ['id', 'order_number', 'menuitem', 'quantity', 'unit_price', 'price']

    def validate_order_number(self, value):
        try:
            # Fetch the Order based on the provided order number
            order = Order.objects.get(order_number=value, user=self.context['request'].user)
            return order
        except Order.DoesNotExist:
            raise serializers.ValidationError("Invalid order number.")

    def create(self, validated_data):
        # Extract 'order_number' from the validated data
        order_number = validated_data.pop('order_number')

        # Fetch the associated 'Order' object
        order = validated_data.pop('order_number')

        # Fetch the associated 'Cart' object
        cart = Cart.objects.get(user=self.context['request'].user, order=order)

        # Populate 'menuitem', 'quantity', 'unit_price', and 'price'
        validated_data['menuitem'] = cart.menuitem
        validated_data['quantity'] = cart.quantity
        validated_data['unit_price'] = cart.unit_price
        validated_data['price'] = cart.price

        # Create the OrderItem instance
        order_item = OrderItem.objects.create(order=order, **validated_data)

        return order_item