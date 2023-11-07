from django.urls import path
from . import views

urlpatterns=[
    path('users/groups', views.ManageUsersView.as_view()),#this comprises of full user management, deletion, creation and grouping- only managers and admin 
    path('new-user', views.CreateUserView.as_view()),
    path('signup', views.CustomerSignUpView.as_view()),
    path('categories', views.CategoriesView.as_view()),
    path('menu-items', views.MenuItemsView.as_view()),
    path('add-menu-item', views.AddMenuItemView.as_view()),
    path('cart',views.CartView.as_view()),#customers view their cart, managers view all carts
    path('orders',views.OrderView.as_view()),#customers view their order, managers and delivery crew view all orders
    #path('all-carts', views.CartView.as_view()),
    path('order-delivery/<int:pk>', views.AssignDeliveryCrewView.as_view()), #update request (PUT)payload e.g. assigned_delivery_crew (give name in database)
    path('order-items', views.OrderItemsView.as_view()),
    
    
]
