from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.contrib.auth.models import Group, User, Permission
from django.contrib.auth import get_user_model

class isManager(BasePermission):
    def permissions(self, request, view):
        return request.User.groups.filter(name='Manager').exists()
    
class isDeliveryCrew(AbstractBaseUser, PermissionsMixin):
    def permissions(self, request, view):
        return request.User.groups.filter(name='Manager'|'Delivery').exists()

class isCustomer(AbstractBaseUser, PermissionsMixin):
    def permissions(self, request, view):
        excluded_groups = ['Manager', 'Delivery Crew']
        return not request.User.groups.filter(name__in =excluded_groups).exists()
    