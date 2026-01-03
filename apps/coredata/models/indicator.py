from django.db import models
from django.utils import timezone


class Indicator(models.Model):
    """
    指标基础信息表（精简版）
    """
    year = models.PositiveIntegerField(
        "指标年份",
        default=timezone.now().year,  # 默认为当前年份
        null=True,                    # 数据库允许NULL
        blank=True,                   # 表单允许为空
        help_text="请输入四位数的年份"   # 帮助文本
    )


    # 指标的省ID
    province_id = models.IntegerField(
        "省id",
        default=0,  # 整数默认值
        help_text="指标的省id",
    )

    # 指标的城市ID
    city_id = models.IntegerField(
        "城市id",
        default=0,  # 整数默认值
        help_text="如：110000（北京市代码）"
    )

    # 数据来源： 数据来源名称或机构
    source = models.CharField(
        "数据来源",
        max_length=50,
        default='未知来源',  
        help_text="指标数据来源名称或机构",
    )

    # 数值： 指标的数值
    value = models.DecimalField(
        "数值",
        max_digits=10,  
        decimal_places=2,  
        default='',
        help_text="指标的数值"
    )


    # 英文名：建议唯一，用作代码/接口标识
    name_en = models.CharField(
        "英文名",
        max_length=50,
        unique=True,
        help_text="指标英文名/代码，如: pm25, gdp_per_capita",
    )

    # 中文名：展示名称
    name_zh = models.CharField(
        "中文名",
        max_length=50,
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