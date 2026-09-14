from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
# Making Resuable method inside the User for Checking Role 
    def has_role(self, role_name):    
        return self.user_roles.filter(
            role__name=role_name
        ).exists()
        
        
            

class Role(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class UserRole(models.Model):
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="user_roles",
    )

    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name="user_roles",
    )

    assigned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="roles_assigned",
    )
    
    assigned_at = models.DateTimeField(auto_now_add=True)   
    
    
    def __str__(self):
        return f"{self.user.username} - {self.role.name}"
    
    
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "role"],
                name="unique_user_role",
            )
        ]