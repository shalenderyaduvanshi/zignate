from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from .views import *

urlpatterns = [

    path('login/', LoginDetailUpdatedByOTPLess.as_view(), name='login-otpless'),
    path('logout/', LogoutAPI.as_view(), name='logout'),
    path('users/', UserView.as_view(), name='user-details'),
    path('search/', SearchListView.as_view(), name='user-list'),
    path('match/', UsersWithinRadiusPostView.as_view(), name='users-within-radius-post'),
    path('user-images/', ImageView.as_view(), name='user-images'),


    path('request/send/', SendRequestView.as_view(), name='send_request'),
    path('request/accept/', AcceptRequestView.as_view(), name='accept_request'),
    path('request/reject/', RejectRequestView.as_view(), name='reject_request'),
    path('requests/received/', ReceivedRequestsView.as_view(), name='received_requests'),
    path('requests/sent/', SentRequestsView.as_view(), name='sent_requests'),
    path('requests/accept/', AcceptedRequestsView.as_view(), name='sent_requests'),

    # path('Register/', RegisterView.as_view(), name='register'),
    # path('users/<uuid:pk>/', UserView.as_view(), name='leave-detail'),
    # path('location/',LocationView.as_view(),name='location'),
    # path('add-package/', AddPackageView.as_view(), name='add-package'),
    # path('swipe/', SwipeView.as_view(), name='swipe'),
    path('payment/', PaymentView.as_view(), name='payment'),
    path('Filter/', FilterPreferencesView.as_view(), name='filter'),
    path('whatsapp-chat/', WhatsAppChatView.as_view(), name='whatsapp_chat'),
    path('requests/', RequestListView.as_view(), name='request-list'),
    # path('send-notification/', send_notification, name='send_notification'),
    # path('update-fcm-token/', update_fcm_token, name='update_fcm_token'),

    #__________________________sahil rana____________________
    path('bookmarks/', BookmarkAPIView.as_view(), name='bookmarks'),
    path('bookmarks/<uuid:user_id>/', BookmarkAPIView.as_view(), name='remove_favorite_user'),

    path('payments/', PaymentView.as_view(), name='payment-list'),
    path('payments/<uuid:pk>/', PaymentView.as_view(), name='payment-detail'),

    path('subscription-plans/', SubscriptionPlanView.as_view(), name='subscription-plan-list'),
    path('subscription-plans/<uuid:pk>/', SubscriptionPlanView.as_view(), name='subscription-plan-detail'),

    path('notification/', NotificationView.as_view(), name='notification'),
]


