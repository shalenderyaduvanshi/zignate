from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import *




User = get_user_model()

# class RegisterSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = User
#         fields = ['username', 'email', 'password', 'mobile_number']
#         extra_kwargs = {'password': {'write_only': True}}
    
#     def create(self, validated_data):
#         user = User.objects.create_user(
#             username=validated_data['username'],
#             email=validated_data['email'],
#             password=validated_data['password'],
#             mobile_number=validated_data.get('mobile_number', '')
#         )
#         return user   
# class LoginSerializer(serializers.Serializer):
#     email = serializers.CharField()
#     password = serializers.CharField(write_only=True)

class UserSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(format='hex')  # or use format='hex_verbose' for hyphenated UUID
    class Meta:
        model= User
        fields = "__all__"

class UserGetSerializer(serializers.ModelSerializer):
    images = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = "__all__"  # Or you can specify the fields manually like ['id', 'username', 'images']

    def get_images(self, user):
        # Fetch images associated with the user
        images = Image.objects.filter(user=user)
        # Serialize the images (you can also use ImageSerializer if you want more detailed image data)
        image_urls = [image.image.url for image in images]
        return image_urls

class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model= Image
        fields=['image']


class MatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Match
        fields = ['user', 'liked_user', 'liked', 'matched', 'created_at']

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['user', 'amount', 'payment_status', 'transaction_id', 'created_at']


class FilterSerializer(serializers.ModelSerializer):
    class Meta:
        model= User
        fields =['preference','age_range','character_type']

class RequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Request
        fields = ['id', 'sender', 'receiver', 'status', 'created_at', 'updated_at']

class UserRequestSerializer(serializers.ModelSerializer):
    images = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = ['id','name','images']  # Or you can specify the fields manually like ['id', 'username', 'images']

    def get_images(self, user):
        # Fetch images associated with the user
        images = Image.objects.filter(user=user)
        # Serialize the images (you can also use ImageSerializer if you want more detailed image data)
        image_urls = [image.image.url for image in images]
        return image_urls
    
class RequestGetSerializer(serializers.ModelSerializer):
    sender = UserRequestSerializer()  # Nesting UserSerializer for sender
    receiver = UserRequestSerializer()  # Nesting UserSerializer for receiver

    class Meta:
        model = Request
        fields = ['id', 'sender', 'receiver', 'status', 'created_at', 'updated_at']

class UserRequestAcceptSerializer(serializers.ModelSerializer):
    images = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = ['id','name','images','mobile_number']  # Or you can specify the fields manually like ['id', 'username', 'images']

    def get_images(self, user):
        # Fetch images associated with the user
        images = Image.objects.filter(user=user)
        # Serialize the images (you can also use ImageSerializer if you want more detailed image data)
        image_urls = [image.image.url for image in images]
        return image_urls
class RequestAcceptGetSerializer(serializers.ModelSerializer):
    sender = UserRequestAcceptSerializer()  # Nesting UserSerializer for sender
    receiver = UserRequestAcceptSerializer()  # Nesting UserSerializer for receiver

    class Meta:
        model = Request
        fields = ['id', 'sender', 'receiver', 'status', 'created_at', 'updated_at']






class BookmarkSerializer(serializers.ModelSerializer):
    favorite_users = UserSerializer(many=True, read_only=True)
    
    class Meta:
        model = Bookmark
        fields = ['id', 'user', 'favorite_users']


# ----------------------------------PERMISSIONS------------------------

class UserPermissionSerializer(serializers.Serializer):
    permissions = serializers.ListField(child=serializers.CharField())


class UserWithPermissionsSerializer(serializers.ModelSerializer):
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'permissions']

    def get_permissions(self, obj):
        """
        Retrieves the codename of each permission assigned to the user.
        """
        return obj.user_permissions.values_list('codename', flat=True)



class InteractionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interaction
        fields = ['user', 'target_user', 'status', 'timestamp']





class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '_all_'

class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription_plan
        fields = '_all_'


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'



