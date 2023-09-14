from django.shortcuts import render
from LittleLemonAPI import models
from rest_framework.response import Response
from rest_framework import generics, permissions, status, serializers
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from .models import MenuItem, Category, Cart, OrderItem, Order
from .serializers import MenuItemSerializer, CategorySerializer, CartSerializer, OrderSerializer, UserSerializer, OrderItemsSerializer
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from .perms import isManager, isDeliveryCrew, isCustomer

# Create your views here.
class CategoriesView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

class MenuItemsView(generics.ListAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    ordering_fields = ['price', 'title']
    filterset_fields = ['price', 'title']
    search_fields = ['title']
    permission_classes = [permissions.IsAuthenticated,]
    
class AddMenuItemView(generics.CreateAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    ordering_fields = ['price', 'title']
    filterset_fields = ['price', 'title']
    search_fields = ['title']
    permission_classes = [isManager]

class CartView(generics.ListCreateAPIView):
    queryset = Cart.objects.all()
    serializer_class=CartSerializer
    search_fields=['menuitem']
    permission_classes = [IsAuthenticated]
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cart = serializer.save()
        return Response(CartSerializer(cart).data, status=status.HTTP_201_CREATED)

class OrderView(generics.ListCreateAPIView):
    queryset=Order.objects.all()
    serializer_class=OrderSerializer
    ordering_fields=['date', 'status']
    filterset_fields=['status']
    permission_classes = [IsAuthenticated]
    
class OrderItemsView(generics.ListAPIView):
    queryset=OrderItem.objects.all()
    serializer_class= OrderItemsSerializer
    ordering_fields=['order']

    def get_queryset(self):
        return OrderItem.objects.filter(user=self.request.user)

class CreateOrder(generics.CreateAPIView):
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemsSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def perform_create(self, serializer):
        user_cart = Cart.objects.filter(user=self.request.user)
        items = [cart.menuitem for cart in user_cart]
        serializer.save(user=self.request.user, items=items)
        user_cart.delete()