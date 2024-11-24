from django.contrib.auth import authenticate
from django.db.models import Q
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.generics import ListAPIView
from rest_framework.views import APIView
from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated ,AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from .models import *
from .serializers import *
import requests
from django.contrib.auth import get_user_model
from geopy.distance import geodesic
from math import radians, sin, cos, sqrt, atan2
from collections import OrderedDict
from rest_framework.pagination import PageNumberPagination

User = get_user_model()

class UsersWithinRadiusPagination(PageNumberPagination):
    page_size = 1  # Adjust this to control how many results per page

# class RegisterView(APIView):
#     def post(self, request):
#         serializer = RegisterSerializer(data=request.data)
#         if serializer.is_valid():
#             user = serializer.save()
#             token, created = Token.objects.get_or_create(user=user)
#             return Response({
#                 'token': token.key,
#                 'user': {
#                     'id': user.id,
#                     'username': user.username,
#                     'email': user.email,
#                     'mobile_number': user.mobile_number,
#                 }
#             }, status=status.HTTP_200_OK )
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

import requests
class LoginDetailUpdatedByOTPLess(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = UserGetSerializer

    def post(self, request, *args, **kwargs):
        # Get the mobile number from the request
        mobile_number = request.data.get('mobile_number', None)

        if not mobile_number:
            return Response({'message': "Mobile number is required!"}, status=status.HTTP_400_BAD_REQUEST)

        # ======================= User creation or login =======================
        user, created = User.objects.get_or_create(mobile_number=mobile_number,username=mobile_number)

        # Check if it's the user's first login
        first_login = user.is_first_login

        if first_login:
            # Set is_first_login to False after the first login
            user.is_first_login = False
            user.save()

        # Serialize the user data (without validation, just to return the response)
        serializer = self.serializer_class(user)

        # Generate token for the user
        token, _ = Token.objects.get_or_create(user=user)

        # Return success response with token and user data
        return Response(
            {
                "message": "Login Successfully!",
                'token': token.key,
                "data": serializer.data,
                "first_login": first_login  # Include the first_login status in the response
            },
            status=status.HTTP_200_OK
        )
class SendRequestView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = RequestSerializer

    def post(self, request, *args, **kwargs):
        sender = request.user
        receiver_id = request.data.get('receiver_id')

        try:
            receiver = User.objects.get(id=receiver_id)
        except User.DoesNotExist:
            return Response({'message': 'Receiver not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Check if request already exists
        if Request.objects.filter(sender=sender, receiver=receiver, status='pending').exists():
            return Response({'message': 'Request already sent.'}, status=status.HTTP_400_BAD_REQUEST)

        request_obj = Request.objects.create(sender=sender, receiver=receiver, status='pending')
        serializer = self.get_serializer(request_obj)
        return Response(serializer.data, status=status.HTTP_200_OK )

# Accept a request
class AcceptRequestView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = RequestSerializer

    def post(self, request, *args, **kwargs):
        sender_id = request.data.get('sender_id')

        try:
            request_obj = Request.objects.get(sender_id=sender_id, receiver=request.user, status='pending')
        except Request.DoesNotExist:
            return Response({'message': 'Request not found.'}, status=status.HTTP_404_NOT_FOUND)

        request_obj.accept()
        serializer = self.get_serializer(request_obj)
        return Response(serializer.data, status=status.HTTP_200_OK)

# Reject a request
class RejectRequestView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = RequestSerializer

    def post(self, request, *args, **kwargs):
        sender_id = request.data.get('sender_id')

        try:
            request_obj = Request.objects.get(sender_id=sender_id, receiver=request.user, status='pending')
        except Request.DoesNotExist:
            return Response({'message': 'Request not found.'}, status=status.HTTP_404_NOT_FOUND)

        request_obj.reject()
        serializer = self.get_serializer(request_obj)
        return Response(serializer.data, status=status.HTTP_200_OK)

class StandardPagination(PageNumberPagination):
    page_size = 20  # Set the number of items per page

# Received requests view with pagination
class ReceivedRequestsView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = RequestGetSerializer
    pagination_class = StandardPagination  # Use the standard pagination class

    def get(self, request, *args, **kwargs):
        # Get all requests where the current user is the receiver
        received_requests = Request.objects.filter(receiver=request.user)
        # Apply pagination
        page = self.paginate_queryset(received_requests)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        # Fallback if pagination is not applied
        serializer = self.get_serializer(received_requests, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

# Sent requests view with pagination
class SentRequestsView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = RequestGetSerializer
    pagination_class = StandardPagination  # Use the standard pagination class

    def get(self, request, *args, **kwargs):
        # Get all requests where the current user is the sender
        sent_requests = Request.objects.filter(sender=request.user)
        # Apply pagination
        page = self.paginate_queryset(sent_requests)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        # Fallback if pagination is not applied
        serializer = self.get_serializer(sent_requests, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

# Accepted requests view with pagination
class AcceptedRequestsView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = RequestAcceptGetSerializer
    pagination_class = StandardPagination  # Use the standard pagination class

    def get(self, request, *args, **kwargs):
        # Filter requests where the current user is either the sender or the receiver
        # and where the status is 'accepted' to indicate both sides have accepted
        accepted_requests = Request.objects.filter(
            (models.Q(sender=request.user) | models.Q(receiver=request.user)),
            status='accepted'
        )
        # Apply pagination
        page = self.paginate_queryset(accepted_requests)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        # Fallback if pagination is not applied
        serializer = self.get_serializer(accepted_requests, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class LogoutAPI(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        try:
            request.user.auth_token.delete()
        except AttributeError:
            pass
        return Response({"message": "Logged-Out Successfully"},status=status.HTTP_200_OK)

class UserView(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes=[IsAuthenticated]                                                                

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
      
    def get(self, request, *args, **kwargs):
        user_id = request.query_params.get('user_id')
        if user_id:
            try:
                obj = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        else:
            obj = User.objects.get(id=request.user.id)
        serializer = UserGetSerializer(obj)
        return Response({'message': 'Profile fetched successfully', 'data': serializer.data},status=status.HTTP_200_OK)
    
    def patch(self, request, *args, **kwargs):
        user = request.user
        serializer = self.serializer_class(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
# class LocationView(APIView):
#     queryset = Location.objects.all()
#     serializer_class = LocationSerializer
#     permission_classes=[IsAuthenticated]


#     def post(self, request):
#         serializer = LocationSerializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_200_OK )
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ImageView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Image.objects.all()
    serializer_class = ImageSerializer
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        images = request.FILES.getlist('images')

        # Validate the number of images
        if len(images) < 3 or len(images) > 6:
            return Response(
                {"error": "You must upload between 3 and 6 images."},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = request.user

        # Delete existing images for the user (both from DB and storage)
        Image.objects.filter(user=user).delete()

        # Process and save each uploaded image
        uploaded_images = []
        for image in images:
            image_upload = Image(image=image, user=user)
            image_upload.save()
            uploaded_images.append(image_upload)

        # Serialize and return the uploaded images
        serializer = self.get_serializer(uploaded_images, many=True)
        return Response(
            {"message": "Images uploaded successfully", "data": serializer.data},
            status=status.HTTP_200_OK
        )

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def patch(self, request, *args, **kwargs):
        images = request.FILES.getlist('images')  # Get the list of uploaded images
        user = request.user  # Get the authenticated user
        
        # Get existing images for the user
        existing_images = Image.objects.filter(user=user)
        total_images_count = existing_images.count() + len(images)

        # Validate the number of images (total should not exceed 6)
        if total_images_count > 6:
            return Response(
                {"error": "You can only upload up to 6 images in total."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update existing images if within the limit
        uploaded_images = []
        for image in images:
            image_upload = Image(image=image, user=user)
            image_upload.save()
            uploaded_images.append(image_upload)

        # Optionally remove or replace existing images (e.g., based on some logic)
        # Example: If you want to replace all old images with new ones
        if request.data.get('replace_existing', False):
            # Delete all existing images for the user before adding new ones
            existing_images.delete()

        # Serialize and return all images (new + old)
        updated_queryset = Image.objects.filter(user=user)
        serializer = self.get_serializer(updated_queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class PaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Get payment details from the request
        match_id = request.data.get('match_id')
        amount = request.data.get('amount')
        
        # Simulate payment gateway logic here (or call an external API)
        # For simplicity, assume payment is successful
        payment = Payment.objects.create(
            user=request.user,
            match_id=match_id,
            amount=amount,
            payment_status=True,
            transaction_id="SAMPLE_TXN_ID"  # This would be the real transaction ID from the gateway
        )
        payment.save()

        return Response({'status': 'payment successful', 'transaction_id': payment.transaction_id}, status=200)


class FilterPreferencesView(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all()
    serializer_class = FilterSerializer

    def get_object(self):
        return User.objects.get(user=self.request.user)

class WhatsAppChatView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        match_id = request.data.get('match_id')

        # Check if there's a valid match
        match = Match.objects.filter(id=match_id, matched=True).first()
        if not match:
            return Response({'error': 'No valid match found'}, status=400)

        # Check if the payment is successful for the match
        payment = Payment.objects.filter(match=match, payment_status=True).first()
        if not payment:
            return Response({'error': 'Payment required to initiate chat'}, status=400)

        # Generate WhatsApp link
        phone_number = match.liked_user.mobile_number  # Assuming liked_user has their WhatsApp linked to this number
        whatsapp_link = f"https://wa.me/{phone_number}"

        return Response({'whatsapp_link': whatsapp_link}, status=200)
from decimal import Decimal


"""
class UsersWithinRadiusPostView(APIView):
    permission_classes = [IsAuthenticated]

    def filter_search(self, request):
        # Retrieve filter parameters from the request
        looking_mate = request.data.get("looking_mate")
        gender = request.data.get("gender")
        age_range = request.data.get("age_range")
        height = request.data.get("height")
        religion = request.data.get("religion")
        language = request.data.get("language")
        drink = request.data.get("drink")
        smoke = request.data.get("smoke")
        exercise = request.data.get("exercise")
        relationship_status = request.data.get("relationship_status")
        hobbies = request.data.get("hobbies")
       
        search_filter = {}

        # Add filters to the search criteria
        if looking_mate:
            search_filter['looking_mate'] = looking_mate
        if gender:
            search_filter['gender'] = gender
        if age_range:
            search_filter['age_range'] = age_range
        if height:
            search_filter['height'] = height
        if religion:
            search_filter['religion'] = religion
        if language:
            search_filter['language'] = language
        if drink:
            search_filter['drink'] = drink
        if smoke:
            search_filter['smoke'] = smoke
        if exercise:
            search_filter['exercise'] = exercise
        if relationship_status:
            search_filter['relationship_status'] = relationship_status
        if hobbies:
            search_filter['hobbies'] = hobbies
       
        return search_filter

    def is_valid_coordinates(self, latitude, longitude):
        # Validate if the coordinates are valid numbers and in the range
        try:
            latitude = float(latitude)
            longitude = float(longitude)
        except (ValueError, TypeError):
            return False

        if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
            return False

        return True

    def post(self, request):
        # Step 1: Get the search filters
        search_filter = self.filter_search(request)
        search_filter["profile_active"] = True

        # Step 2: Apply filters to the queryset, excluding the authenticated user
        user = request.user
        all_users_query = User.objects.filter(profile_active=True).exclude(id=user.id)

        # Split users into two lists based on whether they match the filters or not
        matching_users = all_users_query.filter(**search_filter)
        non_matching_users = all_users_query.exclude(id__in=matching_users.values_list('id', flat=True))

        # Step 3: Get the authenticated user's location
        if not self.is_valid_coordinates(user.latitude, user.longitude):
            return Response({'error': 'Authenticated user does not have valid coordinates.'}, status=status.HTTP_400_BAD_REQUEST)

        user_lat = float(user.latitude)
        user_lng = float(user.longitude)
        current_location = (user_lat, user_lng)

        users_within_5km = []
        users_outside_5km = []

        # Helper function to categorize users based on distance
        def categorize_users(user_queryset):
            for user_location in user_queryset:
                if not self.is_valid_coordinates(user_location.latitude, user_location.longitude):
                    continue

                user_location_coords = (float(user_location.latitude), float(user_location.longitude))
                distance = geodesic(current_location, user_location_coords).kilometers

                user_data = UserGetSerializer(user_location).data
                user_info = {
                    "user": user_data,
                    "distance": distance
                }
                if distance < 5:
                    users_within_5km.append(user_info)
                else:
                    users_outside_5km.append(user_info)

        # Step 4: Categorize matching users first, then non-matching users
        categorize_users(matching_users)
        categorize_users(non_matching_users)

        # Step 5: Combine the lists, with users within 5 km at the top
        all_users_sorted = users_within_5km + users_outside_5km

        # Pagination
        paginator = UsersWithinRadiusPagination()
        paginated_users = paginator.paginate_queryset(all_users_sorted, request)

        return paginator.get_paginated_response({'users_within_radius': paginated_users})

"""

class UsersWithinRadiusPostView(APIView):
    permission_classes = [IsAuthenticated]

    def filter_search(self, request):
        # Retrieve filter parameters from the request
        looking_mate = request.data.get("looking_mate")
        gender = request.data.get("gender")
        age_range = request.data.get("age_range")
        height = request.data.get("height")
        religion = request.data.get("religion")
        language = request.data.get("language")
        drink = request.data.get("drink")
        smoke = request.data.get("smoke")
        exercise = request.data.get("exercise")
        relationship_status = request.data.get("relationship_status")
        hobbies = request.data.get("hobbies")
       
        search_filter = {}

        # Add filters to the search criteria
        if looking_mate:
            search_filter['looking_mate'] = looking_mate
        if gender:
            search_filter['gender'] = gender
        if age_range:
            search_filter['age_range'] = age_range
        if height:
            search_filter['height'] = height
        if religion:
            search_filter['religion'] = religion
        if language:
            search_filter['language'] = language
        if drink:
            search_filter['drink'] = drink
        if smoke:
            search_filter['smoke'] = smoke
        if exercise:
            search_filter['exercise'] = exercise
        if relationship_status:
            search_filter['relationship_status'] = relationship_status
        if hobbies:
            search_filter['hobbies'] = hobbies
       
        return search_filter

    def is_valid_coordinates(self, latitude, longitude):
        # Validate if the coordinates are valid numbers and in the range
        try:
            latitude = float(latitude)
            longitude = float(longitude)
        except (ValueError, TypeError):
            return False

        if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
            return False

        return True
    
    def post(self, request):
        # Step 1: Get the search filters
        search_filter = self.filter_search(request)
        search_filter["profile_active"] = True

        # Step 2: Exclude users already present in Interaction for the authenticated user
        user = request.user
        interacted_user_ids = Interaction.objects.filter(user=user).values_list('target_user_id', flat=True)
        all_users_query = User.objects.filter(profile_active=True).exclude(id__in=interacted_user_ids).exclude(id=user.id)

        # Separate matching and non-matching users
        matching_users = all_users_query.filter(**search_filter)
        non_matching_users = all_users_query.exclude(id__in=matching_users.values_list('id', flat=True))

        # Step 3: If there are matching users, store the first one in Interaction
        if matching_users.exists():
            first_match = matching_users.first()

            n = 4  # Set the threshold 'n'
            interaction_count = Interaction.objects.filter(user=user).count()

            # If the count exceeds 'n', delete the first added interaction
            if interaction_count >= n:
                first_interaction = Interaction.objects.filter(user=user).order_by('id').first()
                first_interaction.delete()

            Interaction.objects.get_or_create(user=user, target_user=first_match)

        # Step 4: Check the authenticated user's location
        if not self.is_valid_coordinates(user.latitude, user.longitude):
            return Response({'error': 'Authenticated user does not have valid coordinates.'}, status=status.HTTP_400_BAD_REQUEST)

        user_lat = float(user.latitude)
        user_lng = float(user.longitude)
        current_location = (user_lat, user_lng)

        users_within_5km = []
        users_outside_5km = []

        def categorize_users(user_queryset):
            for user_location in user_queryset:
                if not self.is_valid_coordinates(user_location.latitude, user_location.longitude):
                    continue

                user_location_coords = (float(user_location.latitude), float(user_location.longitude))
                distance = geodesic(current_location, user_location_coords).kilometers
                user_data = UserGetSerializer(user_location).data
                user_info = {"user": user_data, "distance": distance}
                
                if distance < 5:
                    users_within_5km.append(user_info)
                else:
                    users_outside_5km.append(user_info)

        # Step 5: Categorize matching and non-matching users by distance
        categorize_users(matching_users)
        categorize_users(non_matching_users)

        # Step 6: Combine the lists, with users within 5 km at the top
        all_users_sorted = users_within_5km + users_outside_5km

        # Pagination
        paginator = UsersWithinRadiusPagination()
        paginated_users = paginator.paginate_queryset(all_users_sorted, request)
        
        return paginator.get_paginated_response({'users_within_radius': paginated_users})
    
# class UsersWithinRadiusPostView(APIView):
#     permission_classes = [IsAuthenticated]

#     def filter_search(self, request):
#         # Retrieve filter parameters from the request
#         looking_mate = request.data.get("looking_mate")
#         gender = request.data.get("gender")
#         age_range = request.data.get("age_range")
#         height = request.data.get("height")
#         religion = request.data.get("religion")
#         language = request.data.get("language")
#         drink = request.data.get("drink")
#         smoke = request.data.get("smoke")
#         exercise = request.data.get("exercise")
#         relationship_status = request.data.get("relationship_status")
#         hobbies = request.data.get("hobbies")
        
#         search_filter = {}

#         # Add filters to the search criteria
#         if looking_mate:
#             search_filter['looking_mate'] = looking_mate
#         if gender:
#             search_filter['gender'] = gender
#         if age_range:
#             search_filter['age_range'] = age_range
#         if height:
#             search_filter['height'] = height
#         if religion:
#             search_filter['religion'] = religion
#         if language:
#             search_filter['language'] = language
#         if drink:
#             search_filter['drink'] = drink
#         if smoke:
#             search_filter['smoke'] = smoke
#         if exercise:
#             search_filter['exercise'] = exercise
#         if relationship_status:
#             search_filter['relationship_status'] = relationship_status
#         if hobbies:
#             search_filter['hobbies'] = hobbies
        
#         return search_filter

#     def is_valid_coordinates(self, latitude, longitude):
#         try:
#             latitude = float(latitude)
#             longitude = float(longitude)
#         except (ValueError, TypeError):
#             return False

#         if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
#             return False

#         return True

#     def post(self, request):
#         # Step 1: Get the search filters
#         search_filter = self.filter_search(request)
#         search_filter["profile_active"] = True

#         # Step 2: Apply filters to the queryset, excluding the authenticated user
#         user = request.user
#         all_users_query = User.objects.filter(profile_active=True).exclude(id=user.id)

#         # Split users into two lists based on whether they match the filters or not
#         matching_users = all_users_query.filter(**search_filter)
#         non_matching_users = all_users_query.exclude(id__in=matching_users.values_list('id', flat=True))

#         # Step 3: Get the authenticated user's location
#         if not self.is_valid_coordinates(user.latitude, user.longitude):
#             return Response({'error': 'Authenticated user does not have valid coordinates.'}, status=status.HTTP_400_BAD_REQUEST)

#         user_lat = float(user.latitude)
#         user_lng = float(user.longitude)
#         current_location = (user_lat, user_lng)

#         # Step 4: Lists to categorize users and track interactions
#         users_within_5km = []
#         users_outside_5km = []
#         interacted_users = []
#         rejected_users = []

#         # Helper function to categorize users based on distance and interaction
#         def categorize_users(user_queryset):
#             for user_location in user_queryset:
#                 if not self.is_valid_coordinates(user_location.latitude, user_location.longitude):
#                     continue

#                 user_location_coords = (float(user_location.latitude), float(user_location.longitude))
#                 distance = geodesic(current_location, user_location_coords).kilometers

#                 user_data = UserGetSerializer(user_location).data
#                 user_info = {
#                     "user": user_data,
#                     "distance": distance
#                 }
#                 # Track interactions
#                 if some_interaction_condition(user_location):  # Implement logic for interaction
#                     interacted_users.append(user_info)
#                 elif some_rejection_condition(user_location):  # Implement logic for rejection
#                     rejected_users.append(user_info)
#                 else:
#                     if distance < 5:
#                         users_within_5km.append(user_info)
#                     else:
#                         users_outside_5km.append(user_info)

#         # Step 5: Categorize matching users first, then non-matching users
#         categorize_users(matching_users)
#         categorize_users(non_matching_users)

#         # After interacting with all users, add rejected users back to the main list
#         all_users_sorted = users_within_5km + users_outside_5km + interacted_users + rejected_users

#         # Pagination
#         paginator = UsersWithinRadiusPagination()
#         paginated_users = paginator.paginate_queryset(all_users_sorted, request)

#         return paginator.get_paginated_response({'users_within_radius': paginated_users})



class SearchListView(ListAPIView):
    serializer_class = UserGetSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        keyword = self.request.query_params.get('search', None)
        queryset = User.objects.all()

        if keyword:
            queryset = queryset.filter(
                Q(name__icontains=keyword) |
                Q(age__icontains=keyword) |
                Q(preference__icontains=keyword) |
                Q(character_type__icontains=keyword) |
                Q(state__icontains=keyword) |
                Q(nationality__icontains=keyword) |
                Q(age_range__icontains=keyword) |
                Q(gender_interest__icontains=keyword) |
                Q(religion__icontains=keyword) |
                Q(looking_mate__icontains=keyword)
            ).distinct()
        return queryset



class RequestListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        sent_requests = Request.objects.filter(sender=request.user)
        received_requests = Request.objects.filter(receiver=request.user)

        sent_serializer = RequestSerializer(sent_requests, many=True)
        received_serializer = RequestSerializer(received_requests, many=True)

        return Response({
            'sent_requests': sent_serializer.data,
            'received_requests': received_serializer.data,
        })


###################### NOTIFICTION ############################################

# def send_notification(request):
#     if request.method == "POST":
#         sender_id = request.POST.get('sender_id')
#         receiver_id = request.POST.get('receiver_id')
#         message_text = request.POST.get('message')

#         # Get the FCM token of the receiver
#         try:
#             receiver = User.objects.get(id=receiver_id)
#             fcm_token = receiver.fcm_token
#         except User.DoesNotExist:
#             return JsonResponse({'error': 'Receiver not found'}, status=404)

#         # Create the notification payload
#         message = messaging.Message(
#             notification=messaging.Notification(
#                 title='New Friend Request',
#                 body=f"{sender_id} sent you a request!",
#             ),
#             token=fcm_token,
#         )

#         # Send the notification via Firebase
#         try:
#             response = messaging.send(message)
#             return JsonResponse({'message': 'Notification sent', 'response': response})
#         except Exception as e:
#             return JsonResponse({'error': str(e)}, status=500)


# def update_fcm_token(request):
#     if request.method == 'POST':
#         user_id = request.POST.get('user_id')
#         fcm_token = request.POST.get('fcm_token')

#         try:
#             user = User.objects.get(id=user_id)
#             user.fcm_token = fcm_token
#             user.save()
#             return JsonResponse({'message': 'Token updated successfully'})
#         except User.DoesNotExist:
#             return JsonResponse({'error': 'User not found'}, status=404)


# ================================like===============================
class BookmarkPagination(PageNumberPagination):
    page_size = 20  
    page_size_query_param = 'page_size'
    max_page_size = 100

class  BookmarkAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            bookmark = Bookmark.objects.get(user=user)
            favorite_users = bookmark.favorite_users.exclude(id=user.id)

            paginator = BookmarkPagination()
            paginated_users = paginator.paginate_queryset(favorite_users, request, view=self)

            # Serialize only the paginated users
            serializer = UserGetSerializer(paginated_users, many=True)

            # Return paginated response with metadata
            return paginator.get_paginated_response(serializer.data)

        except Bookmark.DoesNotExist:
            return Response({'favorite_users': []}, status=status.HTTP_200_OK)

    def post(self, request):
        # Get the user_id from the request body
        user_id = request.data.get('user_id')
        if user_id is None:
            return Response({'error': 'user_id is required.'}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        # Validate that the user exists
        try:
            favourite = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Retrieve or create the Bookmark for the current user
        bookmark, created = Bookmark.objects.get_or_create(user=user)

        # Add the user to the favorite users list if they are not already added
        if favourite in bookmark.favorite_users.all():
            return Response({'message': 'User is already in the favorites list.'}, status=status.HTTP_400_BAD_REQUEST)
        bookmark.favorite_users.add(favourite)

        # Prepare response data using the UserSerializer
        serializer = UserSerializer(favourite)
        return Response({'favorite_user_added': serializer.data}, status=status.HTTP_201_CREATED)
    

    def delete(self, request, user_id=None):
        try:
            user = request.user
            bookmark = Bookmark.objects.get(user=user)

            if user_id is not None:
                # Try to find the user to remove from favorites
                try:
                    user_to_remove = User.objects.get(id=user_id)
                except User.DoesNotExist:
                    return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

                # Remove the specific favorite user
                if user_to_remove in bookmark.favorite_users.all():
                    bookmark.favorite_users.remove(user_to_remove)
                    return Response({'message': f'User {user_id} removed from favorites.'}, status=status.HTTP_200_OK)
                else:
                    return Response({'error': 'User is not in your favorites list.'}, status=status.HTTP_400_BAD_REQUEST)

            else:
                # Clear all favorite users
                bookmark.favorite_users.clear()
                return Response({'message': 'All favorite users removed.'}, status=status.HTTP_200_OK)

        except Bookmark.DoesNotExist:
            return Response({'message': 'No favorite users found for the current user.'}, status=status.HTTP_404_NOT_FOUND)









##############################################################################################
##############################################################################################




# class SwipeView(APIView):

#     def post(self, request):
#         swiper = request.user  # The user making the swipe
#         swiped_user_id = request.data.get('swiped_user_id')
#         liked = request.data.get('liked')

#         try:
#             # Query the user being swiped
#             swiped_user = User.objects.get(id=swiped_user_id)
#         except User.DoesNotExist:
#             return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

#         # Create the swipe action
#         swipe = Swipe.objects.create(swiper=swiper, swiped=swiped_user, liked=liked)

#         # Check if the swiped user already liked the current user (swiper)
#         reverse_swipe = Swipe.objects.filter(swiper=swiped_user, swiped=swiper, liked=True).first()
#         if liked and reverse_swipe:
#             # If both users liked each other, create a match
#             match = Match.objects.create(user1=swiper, user2=swiped_user)
#             return Response({
#                 "message": "It's a match!",
#                 "match": MatchSerializer(match).data
#             }, status=status.HTTP_200_OK )

#         # If no match, return swipe details
#         return Response(SwipeSerializer(swipe).data, status=status.HTTP_200_OK )
# class MatchListView(APIView):
#     # permission_classes = [IsAuthenticated]

#     def get(self, request):
#         user = request.user
#         matches = Match.objects.filter(models.Q(user1=user) | models.Q(user2=user))
#         serializer = MatchSerializer(matches, many=True)
#         return Response(serializer.data)

















# class NearbyUsersView(generics.ListAPIView):
#     serializer_class = GeoLocationSerializer
#     permission_classes = [IsAuthenticated]

#     def get_queryset(self):
#         user_profile = User.objects.get(user=self.request.user)
#         user_lat = user_profile.latitude
#         user_lng = user_profile.longitude

#         # Retrieve the distance parameter from the query string, default to 5 km
#         distance_limit = self.request.query_params.get('distance', 5)  # in kilometers
#         distance_limit = float(distance_limit)

#         nearby_profiles = []
#         for profile in User.objects.exclude(user=self.request.user):
#             dist = self.calculate_distance(user_lat, user_lng, profile.latitude, profile.longitude)
#             if dist <= distance_limit:
#                 nearby_profiles.append(profile)

#         return nearby_profiles

#     def calculate_distance(self, lat1, lon1, lat2, lon2):
#         # Radius of the Earth in kilometers
#         R = 6371.0  
#         lat1_rad = radians(lat1)
#         lon1_rad = radians(lon1)
#         lat2_rad = radians(lat2)
#         lon2_rad = radians(lon2)

#         dlon = lon2_rad - lon1_rad
#         dlat = lat2_rad - lat1_rad

#         a = sin(dlat / 2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2)**2
#         c = 2 * atan2(sqrt(a), sqrt(1 - a))

#         return R * c



# class LoginDetailUpdatedByOTPLess(generics.GenericAPIView):
#     permission_classes=[AllowAny]
#     serializer_class = UserSerializer
#     def post(self,request,*args, **kwargs):
#         otp_less_token = request.data.get('otpless_token',None)
#         if not otp_less_token:
#             return Response({'message':"Invalid Login!"},status=status.HTTP_400_BAD_REQUEST)
#         # =======================otpless api call=================
#         user = User.objects.create_user(mobile_number = "909090909090")
#         serializer = self.serializer_class(user)
#         if serializer.is_valid():
#             serializer.save()
#             if user:
#                 token, created = Token.objects.get_or_create(user=user)

#             return Response({"message":"Login Successfully!",'token': token.key,"data":serializer.data}, status=status.HTTP_200_OK )


class PaymentView(APIView):
    def get(self, request, pk):
        if pk:
            payments = Payment.objects.all()
            serializer = PaymentSerializer(payments, many=True)
            return Response(serializer.data)
        else:
            try:
                payment = Payment.objects.get(pk=pk)
            except Payment.DoesNotExist:
                return Response(status=status.HTTP_404_NOT_FOUND)

            serializer = PaymentSerializer(payment)
            return Response(serializer.data)

    def post(self, request):
        serializer = PaymentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        try:
            payment = Payment.objects.get(pk=pk)
        except Payment.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = PaymentSerializer(payment, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        try:
            payment = Payment.objects.get(pk=pk)
        except Payment.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        payment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SubscriptionPlanView(APIView):
    def get(self, request, pk):
        if pk:
            subscription_plans = Subscription_plan.objects.all()
            serializer = SubscriptionPlanSerializer(subscription_plans, many=True)
            return Response(serializer.data)
        else:
            try:
                subscription_plan = Subscription_plan.objects.get(pk=pk)
            except Subscription_plan.DoesNotExist:
                return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = SubscriptionPlanSerializer(subscription_plan)
        return Response(serializer.data)

    def post(self, request):
        serializer = SubscriptionPlanSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        try:
            subscription_plan = Subscription_plan.objects.get(pk=pk)
        except Subscription_plan.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = SubscriptionPlanSerializer(subscription_plan, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        try:
            subscription_plan = Subscription_plan.objects.get(pk=pk)
        except Subscription_plan.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        subscription_plan.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


