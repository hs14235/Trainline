from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.http import JsonResponse

from core.views import (
    TrainTripViewSet, TicketViewSet, UserDetailView,
    SeatListCreateView, NotificationViewSet,
)
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

router = DefaultRouter()
router.register(r"train-trips", TrainTripViewSet, basename="traintrip")
router.register(r"tickets", TicketViewSet, basename="ticket")
router.register(r"notifications", NotificationViewSet, basename="notification")

urlpatterns = [
    path("admin/", admin.site.urls),

    # health
    path("healthz", lambda r: JsonResponse({"ok": True})),

    # API
    path("api/", include(router.urls)),
    path("api/seats/", SeatListCreateView.as_view(), name="seat-list-create"),
    path("api/me/", UserDetailView.as_view(), name="me"),

    # auth
    path("dj-rest-auth/", include("dj_rest_auth.urls")),
    path("dj-rest-auth/registration/", include("dj_rest_auth.registration.urls")),

    # docs
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]





"""

from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.http import JsonResponse

from core.views import (
    TrainTripViewSet, TicketViewSet, UserDetailView,
    SeatListCreateView, NotificationViewSet
)

from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

router = DefaultRouter()
router.register(r"train-trips", TrainTripViewSet, basename="traintrip")
router.register(r"tickets", TicketViewSet, basename="ticket")
router.register(r"notifications", NotificationViewSet, basename="notification")
# If SeatListCreateView is an APIView, it won't register with router; expose it separately below.

urlpatterns = [
    path("admin/", admin.site.urls),

    # health
    path("healthz", lambda r: JsonResponse({"ok": True})),

    # API
    path("api/", include(router.urls)),
    path("api/seats/", SeatListCreateView.as_view(), name="seat-list-create"),
    path("api/me/", UserDetailView.as_view(), name="me"),

    # OpenAPI schema + Swagger
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]

"""


