from django.db import models


class Province(models.Model):
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=64)

    class Meta:
        verbose_name = "省份"
        verbose_name_plural = "省份"
        ordering = ["code"]

    def __str__(self) -> str:
        return f"{self.code} - {self.name}"


class City(models.Model):
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=64)
    province = models.ForeignKey(
        Province,
        on_delete=models.CASCADE,
        related_name="cities",
    )

    class Meta:
        verbose_name = "城市"
        verbose_name_plural = "城市"
        ordering = ["province__code", "code"]

    def __str__(self) -> str:
        return f"{self.code} - {self.name}"