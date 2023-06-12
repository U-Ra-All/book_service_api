from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from books.models import Book


class Borrowing(models.Model):
    borrow_date = models.DateTimeField()
    expected_return_date = models.DateTimeField()
    actual_return_date = models.DateTimeField(blank=True, null=True)
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="borrowings")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="borrowings"
    )

    def clean(self):
        if self.expected_return_date <= self.borrow_date:
            raise ValidationError(
                "expected_return_date should be later than borrow_date"
            )
        if (
            not self.actual_return_date is None
            and self.actual_return_date <= self.borrow_date
        ):
            raise ValidationError(
                "actual_return_date should be later than borrow_date"
            )

    def save(
        self,
        force_insert=False,
        force_update=False,
        using=None,
        update_fields=None,
    ):
        self.full_clean()
        return super(Borrowing, self).save(
            force_insert, force_update, using, update_fields
        )

    def __str__(self):
        return f"User: {self.user}, book: {self.book}, expected return date: {self.expected_return_date}"
