from django.db import models

from .indicator import Indicator


class ComputedIndicatorRule(models.Model):
    """
    描述一个“计算指标”的规则，比如：
    指标 A = 指标 B + 指标 C，或者 指标 D = B * 权重1 + C * 权重2。
    先占位，后面可以做成 JSON 配置或代码引用。
    """
    indicator = models.OneToOneField(
        Indicator,
        on_delete=models.CASCADE,
        related_name="compute_rule",
        help_text="该规则对应的计算型指标",
    )
    expression = models.TextField(
        help_text="公式表达式（可自定义语法 或 JSON 配置）",
    )

    class Meta:
        verbose_name = "计算指标规则"
        verbose_name_plural = "计算指标规则"

    def __str__(self) -> str:
        return f"Rule for {self.indicator.code}"


class CompositeScoreFormula(models.Model):
    """
    城市综合绩效得分的公式配置。可以做成多个方案（不同年份或版本）。
    """
    name = models.CharField(max_length=64)
    version = models.CharField(max_length=32, default="v1")
    is_active = models.BooleanField(default=True)
    config_json = models.JSONField(
        help_text="保存权重、参与指标等配置，具体格式你自己约定",
    )

    class Meta:
        verbose_name = "综合绩效公式"
        verbose_name_plural = "综合绩效公式"

    def __str__(self) -> str:
        return f"{self.name} ({self.version})"