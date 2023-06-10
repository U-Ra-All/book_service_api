import os

import requests
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from books.models import Book
from borrowings.models import Borrowing
from borrowings.serializers import (
    BorrowingSerializer,
    BorrowingDetailSerializer,
    BorrowingReturnSerializer,
    BorrowingCreateSerializer,
)


class BorrowingViewSet(viewsets.ModelViewSet):
    queryset = Borrowing.objects.all()
    serializer_class = BorrowingSerializer

    def get_serializer_class(self):
        if self.action == "list" or self.action == "retrieve":
            return BorrowingDetailSerializer

        return BorrowingSerializer

    def get_queryset(self):
        is_active = self.request.query_params.get("is_active")
        user_id_str = self.request.query_params.get("user_id")

        queryset = self.queryset

        if is_active:
            queryset = queryset.filter(actual_return_date=None)

        if self.request.user.is_staff and user_id_str:
            queryset = queryset.filter(user_id=int(user_id_str))

        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)

        return queryset

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "is_active",
                type=OpenApiTypes.STR,
                description="Filter by active (not returned) borrowings. "
                "You can use any value for this parameter (ex. ?is_active=sfs)",
            ),
            OpenApiParameter(
                "user_id",
                type=OpenApiTypes.INT,
                description="Filter by user id (ex. ?user_id=2)",
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


def send_message(borrow_date, expected_return_date, book, user):
    url = os.getenv("TELEGRAM_BOT_SEND_MESSAGE_URL")
    params = dict(
        chat_id=os.getenv("TELEGRAM_CHAT_ID"),
        text=f"The borrowing created: "
        f"borrow_date: {borrow_date}, "
        f"expected_return_date: {expected_return_date}, "
        f"book: {book}, "
        f"user: {user}.",
    )

    print("send_message")

    requests.get(url, params=params)


class CreateBorrowingViewSet(APIView):
    serializer_class = BorrowingCreateSerializer
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        borrow_date = serializer.data["borrow_date"]
        expected_return_date = serializer.data["expected_return_date"]
        actual_return_date = serializer.data["actual_return_date"]
        book = get_object_or_404(Book, pk=serializer.data["book"])

        if book.inventory == 0:
            raise ValidationError("The book inventory equals 0!")

        user = self.request.user

        book.inventory = book.inventory - 1
        book.save()

        Borrowing.objects.create(
            borrow_date=borrow_date,
            expected_return_date=expected_return_date,
            actual_return_date=actual_return_date,
            book=book,
            user=user,
        )

        send_message(
            borrow_date=borrow_date,
            expected_return_date=expected_return_date,
            book=book,
            user=user,
        )

        return Response(status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ReturnBorrowingViewSet(APIView):
    serializer_class = BorrowingReturnSerializer
    permission_classes = (IsAdminUser,)

    def post(self, request, pk):
        data = request.data
        serializer = self.serializer_class(data=data)
        serializer.is_valid(raise_exception=True)

        borrowing = get_object_or_404(Borrowing, pk=pk)

        if borrowing.actual_return_date:
            raise ValidationError("The borrowing is already returned")

        borrowing.actual_return_date = serializer.data.get("actual_return_date")
        borrowing.save()

        book = borrowing.book
        book.inventory = book.inventory + 1
        book.save()

        return Response(status=status.HTTP_200_OK)
