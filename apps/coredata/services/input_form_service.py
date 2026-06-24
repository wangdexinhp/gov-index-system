"""
手工录入表单：从数据库加载已保存的指标值（含 Excel 导入数据）。
"""
from __future__ import annotations

import re
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from apps.coredata.management.commands.indicator_zh_en import (
    AREA_INDIMAP,
    INDIMAP,
)
from apps.coredata.indicator_input_methods import get_input_method_display
from apps.coredata.models.indicator import Indicator, IndicatorArea
from apps.coredata.utils.mapper import get_city_name_to_code


def strip_unit_suffix(name: str) -> str:
    text = (name or "").strip().lstrip("#")
    return re.sub(r"\([^)]*\)$", "", text).strip()


def resolve_name_en(display_name: str, indimap: dict) -> Optional[str]:
    base = strip_unit_suffix(display_name)
    if base in indimap:
        return indimap[base]
    if display_name in indimap:
        return indimap[display_name]
    return None


def _format_value(value) -> Optional[str]:
    if value is None or value == "":
        return None
    if isinstance(value, Decimal):
        val = float(value)
        return str(int(val)) if val == int(val) else str(val)
    return str(value)


def _fetch_previous_value(
    model,
    year: int,
    city_id: int,
    name_en: str,
    area: Optional[str] = None,
) -> Optional[str]:
    prev_year = year - 1
    filters = {"year": prev_year, "city_id": city_id, "name_en": name_en}
    if area is not None:
        filters["area"] = area
    row = model.objects.filter(**filters).values_list("value", flat=True).first()
    return _format_value(row)


def get_city_input_form_data(
    year: int,
    cities: List[str],
    indicator_labels: List[str],
) -> Dict[str, Dict[str, dict]]:
    city_name_to_code = get_city_name_to_code()
    name_en_by_label: Dict[str, str] = {}
    for label in indicator_labels:
        name_en = resolve_name_en(label, INDIMAP)
        if name_en:
            name_en_by_label[label] = name_en

    if not name_en_by_label:
        return {}

    city_ids: Dict[str, int] = {}
    for city in cities:
        key = city.replace("市", "")
        cid = city_name_to_code.get(key, 0)
        if cid:
            city_ids[city] = cid

    if not city_ids:
        return {}

    rows = Indicator.objects.filter(
        year=year,
        city_id__in=list(city_ids.values()),
        name_en__in=list(name_en_by_label.values()),
    ).values("city_id", "name_en", "value", "note", "source", "input_method")

    by_city_en: Dict[Tuple[int, str], dict] = {}
    for row in rows:
        by_city_en[(row["city_id"], row["name_en"])] = row

    result: Dict[str, Dict[str, dict]] = {}
    en_to_label = {v: k for k, v in name_en_by_label.items()}

    for city, city_id in city_ids.items():
        city_bucket: Dict[str, dict] = {}
        for label, name_en in name_en_by_label.items():
            record = by_city_en.get((city_id, name_en))
            if not record:
                continue
            city_bucket[label] = {
                "value": _format_value(record["value"]),
                "note": record.get("note") or "",
                "source": record.get("source") or "",
                "input_method": record.get("input_method") or "",
                "input_method_display": get_input_method_display(record.get("input_method")),
                "reference": _fetch_previous_value(
                    Indicator, year, city_id, name_en
                ),
            }
        if city_bucket:
            result[city] = city_bucket

    return result


def get_area_input_form_data(
    year: int,
    area_items: List[dict],
    indicator_labels: List[str],
) -> Dict[str, Dict[str, dict]]:
    """
    area_items: [{"city": "北京市", "area": "朝阳区"}, ...]
    返回 key 为 "城市__区县"
    """
    city_name_to_code = get_city_name_to_code()
    name_en_by_label: Dict[str, str] = {}
    for label in indicator_labels:
        name_en = resolve_name_en(label, AREA_INDIMAP) or resolve_name_en(label, INDIMAP)
        if name_en:
            name_en_by_label[label] = name_en

    if not name_en_by_label or not area_items:
        return {}

    normalized_items: List[Tuple[str, int, str]] = []
    for item in area_items:
        city = (item.get("city") or "").strip()
        area = (item.get("area") or "").strip()
        if not city or not area:
            continue
        city_id = city_name_to_code.get(city.replace("市", ""), 0)
        if city_id:
            normalized_items.append((city, city_id, area))

    if not normalized_items:
        return {}

    city_ids = {cid for _, cid, _ in normalized_items}
    areas = {area for _, _, area in normalized_items}

    rows = IndicatorArea.objects.filter(
        year=year,
        city_id__in=list(city_ids),
        area__in=list(areas),
        name_en__in=list(name_en_by_label.values()),
    ).values("city_id", "area", "name_en", "value", "note", "source", "input_method")

    by_key: Dict[Tuple[int, str, str], dict] = {}
    for row in rows:
        by_key[(row["city_id"], row["area"], row["name_en"])] = row

    result: Dict[str, Dict[str, dict]] = {}
    for city, city_id, area in normalized_items:
        bucket_key = f"{city}__{area}"
        area_bucket: Dict[str, dict] = {}
        for label, name_en in name_en_by_label.items():
            record = by_key.get((city_id, area, name_en))
            if not record:
                continue
            area_bucket[label] = {
                "value": _format_value(record["value"]),
                "note": record.get("note") or "",
                "source": record.get("source") or "",
                "input_method": record.get("input_method") or "",
                "input_method_display": get_input_method_display(record.get("input_method")),
                "reference": _fetch_previous_value(
                    IndicatorArea, year, city_id, name_en, area=area
                ),
            }
        if area_bucket:
            result[bucket_key] = area_bucket

    return result
