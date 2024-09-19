from django.urls import path, include
from rest_framework.routers import DefaultRouter
from borrowings.views import BorrowingViewSet

router = DefaultRouter()
router.register("borrowings", BorrowingViewSet)

urlpatterns = [
    path("", include(router.urls)),
    # path(
    #      "borrowings/<int:pk>/return",
    #      BorrowingViewSet.as_view({"post": "borrow"}),
    #      name="return-borrowing"
    # ),
]

app_name = "borrowings"
