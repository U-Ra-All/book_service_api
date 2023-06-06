from django.db import models


class Book(models.Model):
    class Cover(models.IntegerChoices):
        HARD = 1
        SOFT = 2

    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    cover = models.PositiveSmallIntegerField(choices=Cover.choices, default=Cover.HARD)
    inventory = models.PositiveIntegerField()
    daily_fee = models.DecimalField()
