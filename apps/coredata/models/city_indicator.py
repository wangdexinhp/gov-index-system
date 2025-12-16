from django.conf import settings
from django.db import models

from apps.coredata.models.geography import Province, City
from apps.coredata.models.indicator import Indicator


class CityIndicatorValue(models.Model):
    """
    地市-指标-年份 对应的数值记录
    """

    # 年份
    year = models.PositiveIntegerField("年份")

    # 城市
    city = models.ForeignKey(
        City,
        verbose_name="城市",
        on_delete=models.PROTECT,
        related_name="indicator_values",
    )

    # 省份（冗余字段，方便按省过滤）
    province = models.ForeignKey(
        Province,
        verbose_name="省份",
        on_delete=models.PROTECT,
        related_name="city_indicator_values",
        null=True,
        blank=True,
    )

    # 指标
    indicator = models.ForeignKey(
        Indicator,
        verbose_name="指标",
        on_delete=models.PROTECT,
        related_name="city_values",
    )

    # 数值
    value = models.DecimalField(
        "数值",
        max_digits=20,
        decimal_places=4,
        null=True,
        blank=True,
    )

    # 指标来源
    class Source(models.TextChoices):
        CITY_STAT_YEARBOOK          = "CITY_STAT_YB", "地市统计年鉴"
        CITY_YEARBOOK               = "CITY_YB", "地市年鉴"
        CITY_DEV_BULLETIN           = "CITY_DEV_BUL", "地市级发展公报"
        CITY_GOV_REPORT             = "CITY_GOV_RPT", "地市级政府工作报告"
        PROV_STAT_YEARBOOK          = "PROV_STAT_YB", "省级统计年鉴"
        PROV_YEARBOOK               = "PROV_YB", "省级年鉴"
        PROFESSIONAL_YEARBOOK       = "PROF_YB", "专业年鉴"
        SPECIAL_REPORT              = "SPECIAL_RPT", "专项报告"
        GOV_INFO_DISCLOSURE_REPORT  = "GOV_INFO_RPT", "政府信息公开报告"

    source = models.CharField(
        "指标来源",
        max_length=32,
        choices=Source.choices,
        blank=True,
        null=True,
    )

    # 备注（文本）
    remark = models.TextField(
        "备注",
        blank=True,
        null=True,
    )

    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)
    last_year_value = models.DecimalField(
        max_digits=20,  # 总位数，比如 9999999999999999.9999 就是 20
        decimal_places=4,  # 小数位数，比如保留四位小数
        null=True,
        blank=True,
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,  # 注意：没有括号！
        null=True,
        blank=True,
        related_name="updated_city_indicator_values",  # 可选，防止 related_name 冲突
    )

    class Meta:
        verbose_name = "城市指标值"
        verbose_name_plural = "城市指标值"
        unique_together = ("year", "city", "indicator")
        ordering = ["-year", "city"]

    def __str__(self):
        return f"{self.year}年 {self.city.name} {self.indicator.name_zh}: {self.value}"