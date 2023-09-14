from django.urls import path
from . import views

urlpatterns=[
    path('menu-items', views.MenuItemsView.as_view()),
    path('my-cart',views.CartView.as_view()),
    path('order-item',views.CreateOrder.as_view()),
    path('all-carts', views.CartView.as_view()),
    path('add-menu-item', views.AddMenuItemView.as_view()),
]
