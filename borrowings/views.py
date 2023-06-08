from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from books.models import Book
from borrowings.models import Borrowing
from borrowings.serializers import BorrowingSerializer, BorrowingDetailSerializer


class BorrowingViewSet(viewsets.ModelViewSet):
    queryset = Borrowing.objects.all()
    serializer_class = BorrowingSerializer

    def get_serializer_class(self):
        if self.action == "list" or self.action == "retrieve":
            return BorrowingDetailSerializer

        return BorrowingSerializer


class CreateBorrowingViewSet(APIView):
    serializer_class = BorrowingSerializer
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        expected_return_date = serializer.data["expected_return_date"]
        actual_return_date = serializer.data["actual_return_date"]
        book = get_object_or_404(Book, pk=serializer.data["book"])

        if book.inventory == 0:
            raise ValidationError({"The book inventory equals 0!"})

        user = self.request.user

        book.inventory = book.inventory - 1
        book.save()

        Borrowing.objects.create(
            expected_return_date=expected_return_date,
            actual_return_date=actual_return_date,
            book=book,
            user=user,
        )

        return Response(status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
