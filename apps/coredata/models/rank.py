from django.db import models

from .geography import City
from .indicator import Indicator


class CityRank(models.Model):
    city = models.ForeignKey(
        City,
        on_delete=models.CASCADE,
        related_name="rank_city",
    )
    year = models.PositiveIntegerField()
    indicator = models.ForeignKey(
        Indicator,
        on_delete=models.CASCADE,
        related_name="rank_values",
    )
    value = models.DecimalField(
        max_digits=20,
        decimal_places=4,
        null=True,
        blank=True,
    )

    source_type = models.CharField(
        max_length=32,
        blank=True,
        default="manual",  # manual / excel / api / computed
    )
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "城市指标值"
        verbose_name_plural = "城市指标值"
        unique_together = ("city", "year", "indicator")
        indexes = [
            models.Index(fields=["city", "year"]),
            models.Index(fields=["indicator", "year"]),
        ]

    def __str__(self) -> str:
        return f"{self.city} / {self.year} / {self.indicator.code} = {self.value}"