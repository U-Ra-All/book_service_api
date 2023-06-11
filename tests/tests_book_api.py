from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from books.models import Book
from books.serializers import BookSerializer

BOOK_URL = reverse("books:book-list")


class UnauthenticatedBookApiTest(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()

        Book.objects.create(
            title="Sample title 1",
            author="Sample author 1",
            cover=1,
            inventory=5,
            daily_fee=1.25,
        )

        Book.objects.create(
            title="Sample title 2",
            author="Sample author 2",
            cover=2,
            inventory=10,
            daily_fee=2.25,
        )

    def test_auth_not_required_to_list_books(self):
        response = self.client.get(BOOK_URL)
        books = Book.objects.all()
        serializer = BookSerializer(books, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_auth_not_required_to_get_book_details(self):
        response = self.client.get(BOOK_URL + "1/")
        books = Book.objects.get(pk=1)
        serializer = BookSerializer(books, many=False)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_auth_required_for_book_creation(self):
        payload = {
            "title": "Sample title",
            "author": "Sample author",
            "cover": 1,
            "inventory": 5,
            "daily_fee": 1.25,
        }

        response = self.client.post(BOOK_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedBookApiTest(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test_user@mail.com",
            password="test_password",
        )

        self.client.force_authenticate(self.user)

    def test_admin_auth_required_for_book_creation(self):
        payload = {
            "title": "Sample title",
            "author": "Sample author",
            "cover": 1,
            "inventory": 5,
            "daily_fee": 1.25,
        }

        response = self.client.post(BOOK_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class AdminBookApiTest(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test_user@mail.com", password="test_password", is_staff=True
        )

        self.client.force_authenticate(self.user)

    def test_create_book(self):
        payload = {
            "title": "Sample title",
            "author": "Sample author",
            "cover": 1,
            "inventory": 5,
            "daily_fee": 1.25,
        }

        response = self.client.post(BOOK_URL, payload)
        print(response.data)
        book = Book.objects.get(id=response.data["id"])
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        for key in payload:
            self.assertEqual(payload[key], getattr(book, key))


class BookModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        Book.objects.create(
            title="Sample title",
            author="Sample author",
            cover=1,
            inventory=5,
            daily_fee=1.25,
        )

    def test_title_label(self):
        book = Book.objects.get(id=1)
        field_label = book._meta.get_field("title").verbose_name
        self.assertEqual(field_label, "title")

    def test_author_label(self):
        book = Book.objects.get(id=1)
        field_label = book._meta.get_field("author").verbose_name
        self.assertEqual(field_label, "author")

    def test_cover_label(self):
        book = Book.objects.get(id=1)
        field_label = book._meta.get_field("cover").verbose_name
        self.assertEqual(field_label, "cover")

    def test_inventory_label(self):
        book = Book.objects.get(id=1)
        field_label = book._meta.get_field("inventory").verbose_name
        self.assertEqual(field_label, "inventory")

    def test_daily_fee_label(self):
        book = Book.objects.get(id=1)
        field_label = book._meta.get_field("daily_fee").verbose_name
        self.assertEqual(field_label, "daily fee")

    def test_title_max_length(self):
        book = Book.objects.get(id=1)
        max_length = book._meta.get_field("title").max_length
        self.assertEqual(max_length, 255)

    def test_author_max_length(self):
        book = Book.objects.get(id=1)
        max_length = book._meta.get_field("author").max_length
        self.assertEqual(max_length, 255)

    def test_book_str(self):
        book = Book.objects.get(id=1)
        expected_object_name = f"{book.title}, author {book.author}"
        self.assertEqual(str(book), expected_object_name)
