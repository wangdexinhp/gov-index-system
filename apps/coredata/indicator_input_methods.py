"""
指标录入方式（与数据来源 source 区分）

录入方式：手工 / excel
数据来源：统计年鉴、发展公报等（见 indicator_sources）
"""
from typing import Optional

from django.db import models


class IndicatorInputMethod(models.TextChoices):
    MANUAL = "MANUAL", "手工"
    EXCEL = "EXCEL", "excel"


INPUT_METHOD_LABEL_MAP = {
    choice.value: choice.label for choice in IndicatorInputMethod
}

# 历史数据曾把「手工录入」误写入 source 字段
LEGACY_SOURCE_AS_MANUAL = "INPUT"


def get_input_method_display(code: Optional[str]) -> str:
    if not code:
        return ""
    return INPUT_METHOD_LABEL_MAP.get(code, code)


def normalize_data_source(source: Optional[str]) -> str:
    """去掉误当作数据来源保存的 legacy INPUT 代码。"""
    text = (source or "").strip()
    if text == LEGACY_SOURCE_AS_MANUAL:
        return ""
    return text
