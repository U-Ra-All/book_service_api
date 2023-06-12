from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from books.models import Book
from borrowings.models import Borrowing
from borrowings.serializers import BorrowingSerializer, BorrowingDetailSerializer

BORROWING_URL = reverse("borrowings:borrowing-list")


class UnauthenticatedBorrowingApiTest(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()

    def test_auth_required(self):
        response = self.client.get(BORROWING_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedBorrowingApiTest(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test_user@mail.com",
            password="test_password",
        )

        self.user1 = get_user_model().objects.create_user(
            email="test_user1@mail.com",
            password="test_password1",
        )

        self.book = Book.objects.create(
            title="Sample title",
            author="Sample author",
            cover=1,
            inventory=5,
            daily_fee=1.25,
        )

        self.client.force_authenticate(self.user)

    def test_not_list_other_user_borrowings(self):
        Borrowing.objects.create(
            borrow_date="2023-06-10",
            expected_return_date="2023-06-11",
            actual_return_date="2023-06-12",
            book=self.book,
            user=self.user,
        )

        Borrowing.objects.create(
            borrow_date="2023-06-10",
            expected_return_date="2023-06-12",
            actual_return_date="2023-06-12",
            book=self.book,
            user=self.user1,
        )

        response = self.client.get(BORROWING_URL)
        borrowings = Borrowing.objects.all()
        serializer = BorrowingDetailSerializer(borrowings, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotEqual(response.data, serializer.data)

    def test_not_list_only_own_borrowings(self):
        Borrowing.objects.create(
            borrow_date="2023-06-10",
            expected_return_date="2023-06-11",
            actual_return_date="2023-06-12",
            book=self.book,
            user=self.user,
        )

        Borrowing.objects.create(
            borrow_date="2023-06-10",
            expected_return_date="2023-06-12",
            actual_return_date="2023-06-12",
            book=self.book,
            user=self.user1,
        )

        response = self.client.get(BORROWING_URL)
        borrowings = Borrowing.objects.filter(user=self.user)
        serializer = BorrowingDetailSerializer(borrowings, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_create_borrowing(self):
        payload = {
            "borrow_date": "2023-06-10 21:00:00+00:00",
            "expected_return_date": "2023-06-11 21:00:00+00:00",
            "actual_return_date": "2023-06-12 21:00:00+00:00",
            "book": self.book.id,
        }

        response = self.client.post(BORROWING_URL + "create/", payload)
        borrowing = Borrowing.objects.get(id=1)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        for key in payload:
            if key == "book":
                self.assertEqual(payload[key], getattr(borrowing, key).id)
            else:
                self.assertEqual(
                    payload[key][:10], getattr(borrowing, key).strftime("%Y-%m-%d")
                )

    def test_return_borrowing_not_admin(self):
        borrowing = Borrowing.objects.create(
            borrow_date="2023-06-10",
            expected_return_date="2023-06-11",
            book=self.book,
            user=self.user,
        )

        payload = {
            "actual_return_date": "2023-06-12 21:00:00+00:00",
        }

        url = reverse("borrowings:return", args=[borrowing.id])

        response = self.client.post(url, payload)
        borrowing = Borrowing.objects.get(id=1)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class AdminBorrowingApiTest(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test_user@mail.com", password="test_password", is_staff=True
        )

        self.client.force_authenticate(self.user)

        self.book = Book.objects.create(
            title="Sample title",
            author="Sample author",
            cover=1,
            inventory=5,
            daily_fee=1.25,
        )

    def test_return_borrowing_not_admin(self):
        borrowing = Borrowing.objects.create(
            borrow_date="2023-06-10",
            expected_return_date="2023-06-11",
            book=self.book,
            user=self.user,
        )

        payload = {
            "actual_return_date": "2023-06-12 21:00:00+00:00",
        }

        url = reverse("borrowings:return", args=[borrowing.id])

        response = self.client.post(url, payload)
        borrowing = Borrowing.objects.get(id=1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(
            payload["actual_return_date"][:10],
            getattr(borrowing, "actual_return_date").strftime("%Y-%m-%d"),
        )


class BorrowingModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        user = get_user_model().objects.create_user(
            email="test_user@mail.com",
            password="test_password",
        )

        book = Book.objects.create(
            title="Sample title",
            author="Sample author",
            cover=1,
            inventory=5,
            daily_fee=1.25,
        )

        Borrowing.objects.create(
            borrow_date="2023-06-10",
            expected_return_date="2023-06-11",
            book=book,
            user=user,
        )

    def test_borrow_date_label(self):
        borrowing = Borrowing.objects.get(id=1)
        field_label = borrowing._meta.get_field("borrow_date").verbose_name
        self.assertEqual(field_label, "borrow date")

    def test_expected_return_date_label(self):
        borrowing = Borrowing.objects.get(id=1)
        field_label = borrowing._meta.get_field("expected_return_date").verbose_name
        self.assertEqual(field_label, "expected return date")

    def test_actual_return_date_label(self):
        borrowing = Borrowing.objects.get(id=1)
        field_label = borrowing._meta.get_field("actual_return_date").verbose_name
        self.assertEqual(field_label, "actual return date")

    def test_book_label(self):
        borrowing = Borrowing.objects.get(id=1)
        field_label = borrowing._meta.get_field("book").verbose_name
        self.assertEqual(field_label, "book")

    def test_user_label(self):
        borrowing = Borrowing.objects.get(id=1)
        field_label = borrowing._meta.get_field("user").verbose_name
        self.assertEqual(field_label, "user")

    def test_borrowing_str(self):
        borrowing = Borrowing.objects.get(id=1)
        expected_object_name = (
            f"User: {borrowing.user}, "
            f"book: {borrowing.book}, "
            f"expected return date: {borrowing.expected_return_date}"
        )
        self.assertEqual(str(borrowing), expected_object_name)
