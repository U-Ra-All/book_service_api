from django.urls import path, include
from rest_framework import routers

from borrowings.views import (
    BorrowingViewSet,
    CreateBorrowingViewSet,
    ReturnBorrowingViewSet,
)

router = routers.DefaultRouter()
router.register("", BorrowingViewSet)

urlpatterns = [
    path("create/", CreateBorrowingViewSet.as_view()),
    path(
        "return/<int:pk>/",
        ReturnBorrowingViewSet.as_view(),
        name="return",
    ),
    path("", include(router.urls)),
]

app_name = "borrowings"
