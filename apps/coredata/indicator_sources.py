"""
指标数据来源代码与中文名称的统一映射。
录入表单、校验查询、导出等场景共用，避免各页面重复维护。
"""
from typing import List

from django.db import models


class IndicatorDataSource(models.TextChoices):
    CITY_STAT_YB = "CITY_STAT_YB", "地市统计年鉴"
    CITY_YB = "CITY_YB", "地市年鉴"
    CITY_DEV_BUL = "CITY_DEV_BUL", "地市级发展公报"
    CITY_GOV_RPT = "CITY_GOV_RPT", "地市级政府工作报告"
    PROV_STAT_YB = "PROV_STAT_YB", "省级统计年鉴"
    PROV_YB = "PROV_YB", "省级年鉴"
    PROF_YB = "PROF_YB", "专业年鉴"
    SPECIAL_RPT = "SPECIAL_RPT", "专项报告"
    GOV_INFO_RPT = "GOV_INFO_RPT", "政府信息公开报告"
    INPUT = "INPUT", "手工录入"


SOURCE_LABEL_MAP = {choice.value: choice.label for choice in IndicatorDataSource}

# 录入页下拉框常用选项（与 home.html / input_area.html 一致）
FORM_SOURCE_CHOICES = [
    IndicatorDataSource.CITY_STAT_YB,
    IndicatorDataSource.CITY_YB,
    IndicatorDataSource.PROV_STAT_YB,
    IndicatorDataSource.GOV_INFO_RPT,
]


def get_source_display(source: str) -> str:
    """将来源代码转为中文；未知代码原样返回。"""
    if not source:
        return ""
    return SOURCE_LABEL_MAP.get(source, source)


def get_source_choices() -> List[dict]:
    """返回全部来源，供 API / 前端动态渲染。"""
    return [{"code": c.value, "label": c.label} for c in IndicatorDataSource]


def get_form_source_choices() -> List[dict]:
    """返回录入表单使用的来源选项。"""
    return [{"code": c.value, "label": c.label} for c in FORM_SOURCE_CHOICES]
