from core.views import (
    MeView,
    NotificationViewSet,
    SeatListCreateView,
    TicketViewSet,
    TrainTripViewSet,
)
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter

from .health import liveness, readiness

router = DefaultRouter()
router.register(r"train-trips", TrainTripViewSet, basename="traintrip")
router.register(r"tickets", TicketViewSet, basename="ticket")
router.register(r"notifications", NotificationViewSet, basename="notification")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("healthz", liveness, name="healthz"),
    path("readyz", readiness, name="readyz"),
    path("api/", include(router.urls)),
    path(
        "api/seats/<str:flight_id>/",
        SeatListCreateView.as_view(),
        name="seat-list-create",
    ),
    path("api/me/", MeView.as_view(), name="me"),
    path("api/dj-rest-auth/", include("dj_rest_auth.urls")),
    path("api/dj-rest-auth/registration/", include("dj_rest_auth.registration.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
]
