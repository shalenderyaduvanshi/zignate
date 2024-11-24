from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid
from django.utils import timezone
from django.conf import settings
import os
class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    is_first_login = models.BooleanField(default=True)
    mobile_number = models.CharField(max_length=15, unique=True, null=True, blank=True)
    is_whatsapp_number = models.BooleanField(default=False)
    email = models.EmailField(unique=True,null=True,blank=True)
    name = models.CharField(max_length=255, blank=True)
    age = models.PositiveIntegerField(default=0)
    gender=models.CharField(max_length=15,blank=True,null=True)
    preference = models.CharField(max_length=15,null=True,blank=True)
    character_type=models.CharField(max_length=50,null=True,blank=True )
    address = models.CharField(max_length=255, null=True, blank=True)
    state = models.CharField(max_length=255, blank=True)  
    nationality = models.CharField(max_length=255, blank=True)
    age_range = models.CharField(max_length=20, null=True, blank=True)
    gender_interest = models.CharField(max_length=20,null=True, blank=True )
    description = models.TextField(blank=True, null=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    is_paid_plan = models.BooleanField(default=False)  # To check if user has a paid plan
    whatsapp_visibility_start = models.DateTimeField(null=True, blank=True)  # When the number becomes visible
    whatsapp_visibility_end = models.DateTimeField(null=True, blank=True) 
    package = models.JSONField(null=True,blank=True)  
    education_level = models.CharField(max_length=20,null=True, blank=True)
    religion = models.CharField(max_length=50,null=True, blank=True)
    show_profile=models.CharField(max_length=255,null=True,blank=True)
    fcm_token = models.CharField(max_length=255, blank=True, null=True),
    height=models.CharField(max_length=50,blank=True,null=True)
    hobbies = models.JSONField(blank=True, default=list)  
    language = models.JSONField(blank=True, default=list)
    looking_mate = models.JSONField(blank=True, default=list)
    relationship_status = models.CharField(max_length=255, blank=True, null=True)
    drink = models.CharField(max_length=50, null=True, blank=True)
    smoke = models.CharField(max_length=50, null=True, blank=True)
    exercise = models.CharField(max_length=50, null=True, blank=True)
    job_title = models.CharField(max_length=255, blank=True, null=True)
    package_active = models.BooleanField(default=True)

    
    def __str__(self):
        return f"{self.id} | {self.name}"
    



# class Interaction(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="initiated_interactions")
#     target_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="received_interactions")
#     status = models.CharField(max_length=10, choices=[('accepted', 'Accepted'), ('rejected', 'Rejected')])
#     timestamp = models.DateTimeField(auto_now_add=True)

#     class Meta:
#         unique_together = ('user', 'target_user') 
    
class Bookmark(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookmarks') 
    favorite_users = models.ManyToManyField(User, related_name='favorited_by') 
    def _str_(self):
        return f"{self.user.username}'s bookmarks"
class Image(models.Model):
    user = models.ForeignKey('User', on_delete=models.CASCADE,null=True,blank=True)
    image = models.ImageField(upload_to='user_images/')
    def __str__(self):
        return f"Image for {self.user.username}"
    def delete(self, *args, **kwargs):
        # Delete the file from storage
        if self.image:
            if os.path.isfile(self.image.path):
                os.remove(self.image.path)
        # Call the superclass delete to remove the record from the database
        super().delete(*args, **kwargs)

class Match(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='swiping_user')
    liked_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='liked_user')
    liked = models.BooleanField(default=False)
    matched = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Check if both users liked each other
        if Match.objects.filter(user=self.liked_user, liked_user=self.user, liked=True).exists():
            self.matched = True
            Match.objects.filter(user=self.liked_user, liked_user=self.user).update(matched=True)
        super().save(*args, **kwargs)

class Payment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    match = models.ForeignKey(Match, on_delete=models.CASCADE, null=True, blank=True)  # Link payment to match
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status = models.BooleanField(default=False)  # Change to True after successful payment
    created_at = models.DateTimeField(auto_now_add=True)
    transaction_id = models.CharField(max_length=255)
 

class Request(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]

    sender = models.ForeignKey(User, related_name='sent_requests', on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name='received_requests', on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def accept(self):
        self.status = 'accepted'
        self.save()

    def reject(self):
        self.status = 'rejected'
        self.save()



class Interaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="initiated_interactions")
    target_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="received_interactions")
    # status = models.CharField(max_length=10, choices=[('accepted', 'Accepted'), ('rejected', 'Rejected')])
    # timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'target_user')


class Payment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="payment")
    icon_name = models.CharField(max_length=50, blank=True)
    slogan = models.CharField(max_length=50, blank=True)
    title = models.CharField(max_length=50, blank=True)
    subtitle = models.CharField(max_length=50, blank=True)
    Subscription_plan = models.ForeignKey("Subscription_plan", on_delete=models.CASCADE, related_name="subscription")

    button = models.CharField(max_length=50, blank=True)
    bottom_line = models.CharField(max_length=50, blank=True)

class Subscription_plan(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, blank=True)
    price = models.CharField(max_length=50,blank=True)
    discount = models.CharField(max_length=50, blank=True)
    popular = models.BooleanField(default=False)


class Notification(models.Model):
    title = models.CharField(max_length=250)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user")        #sent user
    message = models.CharField(max_length=250)











