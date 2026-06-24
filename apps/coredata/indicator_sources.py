"""
指标数据来源代码与中文名称的统一映射。
录入表单、校验查询、导出等场景共用，避免各页面重复维护。
"""
from typing import Dict, List, Optional, Tuple

from django.db import models

from apps.coredata.indicator_input_methods import normalize_data_source


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


SOURCE_LABEL_MAP = {choice.value: choice.label for choice in IndicatorDataSource}

# 录入表单选项（与 Excel 颜色标示区一致，不含 INPUT）
FORM_SOURCE_CHOICES = [
    IndicatorDataSource.CITY_STAT_YB,
    IndicatorDataSource.CITY_YB,
    IndicatorDataSource.CITY_DEV_BUL,
    IndicatorDataSource.CITY_GOV_RPT,
    IndicatorDataSource.PROV_STAT_YB,
    IndicatorDataSource.PROV_YB,
    IndicatorDataSource.PROF_YB,
    IndicatorDataSource.SPECIAL_RPT,
    IndicatorDataSource.GOV_INFO_RPT,
]

# scope: city=拼接地市名 | province=拼接省份名 | manual=用户自行填写具体名称
FORM_SOURCE_META: Dict[str, Dict[str, str]] = {
    IndicatorDataSource.CITY_STAT_YB: {"scope": "city", "suffix": "统计年鉴"},
    IndicatorDataSource.CITY_YB: {"scope": "city", "suffix": "年鉴"},
    IndicatorDataSource.CITY_DEV_BUL: {"scope": "city", "suffix": "发展公报"},
    IndicatorDataSource.CITY_GOV_RPT: {"scope": "city", "suffix": "政府工作报告"},
    IndicatorDataSource.PROV_STAT_YB: {"scope": "province", "suffix": "统计年鉴"},
    IndicatorDataSource.PROV_YB: {"scope": "province", "suffix": "年鉴"},
    IndicatorDataSource.PROF_YB: {"scope": "manual", "suffix": "专业年鉴"},
    IndicatorDataSource.SPECIAL_RPT: {"scope": "manual", "suffix": "专项报告"},
    IndicatorDataSource.GOV_INFO_RPT: {"scope": "city", "suffix": "政府信息公开报告"},
}


def compose_source_display_name(
    city: str = "",
    province: str = "",
    source_code: str = "",
) -> str:
    """根据来源类别自动拼接「地市/省份名 + 后缀」。"""
    meta = FORM_SOURCE_META.get(source_code, {})
    scope = meta.get("scope", "manual")
    suffix = meta.get("suffix", SOURCE_LABEL_MAP.get(source_code, ""))
    if scope == "province":
        base = (province or "").strip()
        if not base:
            return suffix
        return base + suffix if not base.endswith(suffix) else base
    if scope == "city":
        base = (city or "").strip()
        if not base:
            return suffix
        return base + suffix if not base.endswith(suffix) else base
    return suffix


def resolve_source_for_form(source_value: str) -> Tuple[str, str]:
    """
    将库中来源值解析为 (类别代码, 展示名称)。
    兼容 Excel 存的代码与手工录入的具体名称。
    """
    text = normalize_data_source(source_value)
    if not text:
        return "", ""
    if text in SOURCE_LABEL_MAP:
        return text, SOURCE_LABEL_MAP[text]
    for code, meta in FORM_SOURCE_META.items():
        suffix = meta.get("suffix", "")
        if suffix and text.endswith(suffix):
            return code, text
    return "", text


def get_source_display(source: str) -> str:
    """将来源代码转为中文；已是具体名称则原样返回。"""
    normalized = normalize_data_source(source)
    if not normalized:
        return ""
    return SOURCE_LABEL_MAP.get(normalized, normalized)


def get_source_choices() -> List[dict]:
    """返回全部来源，供 API / 前端动态渲染。"""
    return [{"code": c.value, "label": c.label} for c in IndicatorDataSource]


def get_form_source_choices() -> List[dict]:
    """返回录入表单使用的来源选项（含自动拼接元数据）。"""
    result = []
    for choice in FORM_SOURCE_CHOICES:
        meta = FORM_SOURCE_META.get(choice.value, {"scope": "manual", "suffix": choice.label})
        result.append({
            "code": choice.value,
            "label": choice.label,
            "scope": meta.get("scope", "manual"),
            "suffix": meta.get("suffix", choice.label),
        })
    return result
