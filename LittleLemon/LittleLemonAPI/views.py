from django.shortcuts import render
from django.contrib.auth.models import Group
from LittleLemonAPI import models
from rest_framework.response import Response
from rest_framework import generics, permissions, status, serializers
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from .models import MenuItem, Category, Cart, OrderItem, Order
from .serializers import MenuItemSerializer, CategorySerializer,CustomerSignUpSerializer, CartSerializer, OrderSerializer, UserSerializer, OrderItemsSerializer, GroupSerializer
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from .perms import IsManager, IsCustomer, IsDeliveryCrew
from rest_framework import status
from django.db.models import Q

# Create your views here.
class CategoriesView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated | (IsAdminUser & IsManager)]  # Allow authenticated users to view, admins and managers to create

    def get(self, request, *args, **kwargs):
        # Return a list of categories for all users (including customers)
        return self.list(request, *args, **kwargs)

    def perform_create(self, serializer):
        user = self.request.user
        if user.groups.filter(name='Manager').exists() or user.is_staff:
            # Managers and admins can create categories
            serializer.save()
        else:
            return Response({"detail": "You are not allowed to perform this request."}, status=403)
        
class CreateUserView(generics.ListCreateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser | IsManager]  # Use a list of permission classes
    queryset = User.objects.all()

    def perform_create(self, serializer):
        # Create the user
        user = serializer.save()

        # Get the group name from the request data (assuming 'group' field in your serializer)
        group_name = self.request.data.get('group', None)

        if group_name:
            try:
                group = Group.objects.get(name=group_name)
                user.groups.add(group)
                return Response(
                    {'detail': f"User '{user.username}' has been added to group '{group.name}'."},
                    status=status.HTTP_201_CREATED
                )
            except Group.DoesNotExist:
                return Response(
                    {'detail': f"Group '{group_name}' does not exist."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        return user

class CustomerSignUpView(generics.CreateAPIView):
    serializer_class = CustomerSignUpSerializer
    permission_classes = []
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        # You can perform additional actions here, such as sending a confirmation email.
        return Response({'detail': 'You have been signed up successfully.'}, status=status.HTTP_201_CREATED)

class ManageUsersView(generics.ListCreateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser | IsManager]  # Allow admins and managers
    queryset = User.objects.all()
    filterset_fields = ['username']
    search_fields = ['username']

    def create(self, request, *args, **kwargs):
        # Get the 'group' field from the request data
        group_name = request.data.get('group', None)

        # Get the user by username from the request data
        username = request.data.get('username', None)
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response(
                {'detail': f"User '{username}' does not exist."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get or create the group
        group, created = Group.objects.get_or_create(name=group_name)

        # Add the user to the group
        user.groups.add(group)

        return Response(
            {'detail': f"User '{user.username}' has been added to group '{group.name}'."},
            status=status.HTTP_201_CREATED
        )
    def get(self, request, *args, **kwargs):
        # Retrieve all groups and serialize them
        groups = Group.objects.all()
        serializer = GroupSerializer(groups, many=True)
        return Response(serializer.data)
    
# class MenuItemsView(generics.ListAPIView):
#     queryset = MenuItem.objects.all()
#     serializer_class = MenuItemSerializer
#     ordering=['price']
#     ordering_fields = ['price']
#     filterset_fields = ['price', 'title']
#     search_fields = ['title']
#     permission_classes = [permissions.IsAuthenticated]

class MenuItemsView(generics.ListAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    ordering_fields = ['price']
    ordering = ['price']
    filterset_fields = ['price', 'title']
    search_fields = ['title']
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['ordering_fields'] = self.ordering_fields
        return context


class AddMenuItemView(generics.CreateAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    ordering_fields = ['price', 'title']
    filterset_fields = ['price', 'title']
    search_fields = ['title']
    permission_classes = [IsManager | IsAdminUser]

class CartView(generics.ListCreateAPIView):
    queryset = Cart.objects.all()
    serializer_class=CartSerializer
    search_fields=['menuitem']
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cart = serializer.save(user=self.request.user)
        return Response(CartSerializer(cart).data, status=status.HTTP_201_CREATED)

    
    def get_queryset(self):
        user = self.request.user

        # Check if the user belongs to the 'Manager' group
        if user.groups.filter(name='Manager').exists():
            # Managers can view all carts
            return Cart.objects.all()
        
        # Regular users can only view their own carts
        return Cart.objects.filter(user=user)
        
class OrderView(generics.ListCreateAPIView):
    queryset=Order.objects.all()
    serializer_class=OrderSerializer
    ordering_fields=['date', 'status']
    filterset_fields=['status']
    permission_classes = [IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        cart = Cart.objects.filter(user=self.request.user)
        items = [cart.menuitem for cart in cart]
        serializer.is_valid(raise_exception=True)
        order=serializer.save(user=self.request.user, items=items)
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)
    
    def get_queryset(self):
        user = self.request.user

        # Check if the user belongs to the 'Manager' group
        if user.groups.filter(Q(name='Manager') | Q(name='Delivery Crew')).exists():
            # Managers can view all carts
            return Order.objects.all()
        
        # Regular users can only view their own carts
        return Order.objects.filter(user=user)
    

    
class AssignDeliveryCrewView(generics.UpdateAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAdminUser | IsManager]  # Allow admins and managers

    def get_queryset(self):
        return Order.objects.all()

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        assigned_delivery_crew_username = request.data.get('assigned_delivery_crew', None)

        if not assigned_delivery_crew_username:
            return Response(
                {'detail': 'Please provide a username for the delivery crew.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            delivery_crew = User.objects.get(username=assigned_delivery_crew_username)

            # Check if the user is a member of the 'Delivery Crew' group
            delivery_crew_group = Group.objects.get(name='Delivery Crew')
            if delivery_crew not in delivery_crew_group.user_set.all():
                return Response(
                    {'detail': f"User '{assigned_delivery_crew_username}' is not a member of the 'Delivery Crew' group."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            instance.delivery_crew = delivery_crew
            instance.save()
            return Response(
                {'detail': f"Delivery crew '{delivery_crew.username}' has been assigned to this order."},
                status=status.HTTP_200_OK
            )
        except User.DoesNotExist:
            return Response(
                {'detail': f"User '{assigned_delivery_crew_username}' does not exist."},
                status=status.HTTP_404_NOT_FOUND
            )
    

class OrderItemsView(generics.ListCreateAPIView):
    serializer_class = OrderItemsSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = OrderItem.objects.all()

        if IsManager().has_permission(self.request, self):
            return queryset

        if IsCustomer().has_permission(self.request, self):
            return queryset.filter(order__user=user)

        return OrderItem.objects.none()

    def perform_create(self, serializer):
        # Assuming 'order' is a required field for creating an OrderItem
        # You might need to adjust this based on your model
        order = serializer.validated_data.get('order')

        # Check permissions before allowing creation
        if IsManager().has_permission(self.request, self) or (IsCustomer().has_permission(self.request, self) and order.user == self.request.user):
            serializer.save()
        else:
            return Response(
                {'detail': "You do not have permission to create this resource."},
                status=status.HTTP_403_FORBIDDEN
            )


