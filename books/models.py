from django.db import models


class Book(models.Model):
    class CoverType(models.TextChoices):
        HARD = "Hard", "Hardcover"
        SOFT = "Soft", "Softcover"

    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    cover = models.CharField(
        max_length=4,
        choices=CoverType,
        default=CoverType.HARD
    )
    inventory = models.PositiveIntegerField()
    daily_fee = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        return f"{self.title}, {self.author}"
