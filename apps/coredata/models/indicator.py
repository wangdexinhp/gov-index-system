from django.db import models


class Indicator(models.Model):
    """
    指标基础信息表（精简版）
    """

    # 英文名：建议唯一，用作代码/接口标识
    name_en = models.CharField(
        "英文名",
        max_length=128,
        unique=True,
        help_text="指标英文名/代码，如: pm25, gdp_per_capita",
    )

    # 中文名：展示名称
    name_zh = models.CharField(
        "中文名",
        max_length=128,
        help_text="指标中文名，如：人均GDP，PM2.5浓度",
    )

    # 指标输入形式：录入型 / 计算型
    class InputForm(models.TextChoices):
        INPUT = "INPUT", "录入型"   # 直接录入
        CALC  = "CALC", "计算型"    # 由其他指标计算

    input_form = models.CharField(
        "指标输入形式",
        max_length=16,
        choices=InputForm.choices,
        help_text="录入型：人工/系统直接录入；计算型：由公式或模型计算",
    )

    # 指标类型：环境、司法等（你可以在这里按需扩展几个常用的）
    class IndicatorType(models.TextChoices):
        ENVIRONMENT = "ENV", "环境"
        JUSTICE     = "JUD", "司法"
        ECONOMY     = "ECO", "经济"
        SOCIETY     = "SOC", "社会"
        GOVERNANCE  = "GOV", "治理"
        OTHER       = "OTH", "其他"

    indicator_type = models.CharField(
        "指标类型",
        max_length=8,
        choices=IndicatorType.choices,
        help_text="如：环境、司法、经济、社会、治理等",
    )

    class Meta:
        verbose_name = "指标"
        verbose_name_plural = "指标"
        ordering = ["indicator_type", "name_en"]

    def __str__(self):
        return f"{self.name_zh} ({self.name_en})"