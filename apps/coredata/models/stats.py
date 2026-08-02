from django.db import models


class CityCompletionStats(models.Model):
    """地市指标录入完成率统计（按年缓存）"""

    city_id = models.IntegerField("城市ID", db_index=True)
    city_name = models.CharField("城市名称", max_length=50)
    province_id = models.IntegerField("省份ID", null=True, blank=True)
    province_name = models.CharField("省份名称", max_length=50, blank=True, default="")
    year = models.IntegerField("年份", db_index=True)
    total_indicators = models.IntegerField("应录入指标总数")
    completed_indicators = models.IntegerField("已录入指标数")
    completion_rate = models.DecimalField("完成率(%)", max_digits=5, decimal_places=2)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "city_completion_stats"
        verbose_name = "地市完成率统计"
        verbose_name_plural = "地市完成率统计"
        unique_together = [("city_id", "year")]
        indexes = [
            models.Index(fields=["year", "completion_rate"], name="idx_ccs_year_rate"),
        ]
        ordering = ["-completion_rate", "city_name"]

    def __str__(self):
        return f"{self.city_name} {self.year} {self.completion_rate}%"


class IndicatorCoverageStats(models.Model):
    """指标在全国地市的覆盖率统计（按年缓存）"""

    indicator_name = models.CharField("指标名称", max_length=100)
    indicator_name_en = models.CharField("指标英文代码", max_length=128)
    indicator_group = models.CharField("指标组", max_length=50, blank=True, default="")
    year = models.IntegerField("年份", db_index=True)
    total_cities = models.IntegerField("应录入城市总数")
    covered_cities = models.IntegerField("已录入城市数")
    coverage_rate = models.DecimalField("覆盖率(%)", max_digits=5, decimal_places=2)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "indicator_coverage_stats"
        verbose_name = "指标覆盖率统计"
        verbose_name_plural = "指标覆盖率统计"
        unique_together = [("indicator_name", "year")]
        indexes = [
            models.Index(fields=["year", "coverage_rate"], name="idx_ics_year_rate"),
            models.Index(fields=["indicator_group", "year"], name="idx_ics_group_year"),
        ]
        ordering = ["-coverage_rate", "indicator_name"]

    def __str__(self):
        return f"{self.indicator_name} {self.year} {self.coverage_rate}%"
