# booking/urls.py

from django.contrib import admin
from django.urls import path, include
from rest_framework import routers

from core.views import TrainTripViewSet, TicketViewSet, UserDetailView, SeatListCreateView, NotificationViewSet

router = routers.DefaultRouter()
router.register(r'trips', TrainTripViewSet, basename="trips")
router.register(r'flights', TrainTripViewSet, basename="flight_compat")
router.register(r'tickets', TicketViewSet, basename='ticket')
router.register(r'notifications', NotificationViewSet, basename='notification')



urlpatterns = [
    path('admin/', admin.site.urls),

    path('api/auth/', include('dj_rest_auth.urls')),
    path('api/auth/registration/', include('dj_rest_auth.registration.urls')),
    path('api/user/', UserDetailView.as_view(), name='user-detail'),
    path('api/seats/<str:flight_id>/', SeatListCreateView.as_view(), name='seat-list-create'),
    path('api/', include(router.urls)),

]