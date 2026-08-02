from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from django.db.models import Count
from django.utils import timezone

from apps.coredata.indicator_catalog import (
    AREA_INDICATOR_CATALOG_GROUPS,
    INDICATOR_CATALOG_GROUPS,
    get_area_group_name_map,
    get_group_name_map,
)
from apps.coredata.indicator_input_methods import (
    get_input_method_display,
    normalize_data_source,
)
from apps.coredata.indicator_sources import get_source_display
from apps.coredata.management.commands.import_china_regions import html_area_Map
from apps.coredata.management.commands.indicator_zh_en import (
    AREA_INDIMAP,
    AREA_INDIMAP_UNIT,
    INDIMAP,
    INDIMAP_UNIT,
)
from apps.coredata.models.indicator import Indicator, IndicatorArea
from apps.coredata.services.coverage_service import (
    get_cities_in_scope,
    get_default_coverage_year,
)

# 与 indicator_catalog 一致的分组名称（20 组）
AUDIT_GROUP_NAMES: Dict[str, str] = get_group_name_map()


def _build_audit_indicators() -> List[Dict[str, str]]:
    """从指标目录构建校验范围，分组与弹窗选择一致。"""
    items: List[Dict[str, str]] = []
    seen_en: set = set()
    for group in INDICATOR_CATALOG_GROUPS:
        for name_zh in group["indicators"]:
            name_en = INDIMAP.get(name_zh)
            if not name_en or name_en in seen_en:
                continue
            seen_en.add(name_en)
            items.append({
                "name_zh": name_zh,
                "name_en": name_en,
                "group": group["code"],
            })
    return items


ALL_AUDIT_INDICATORS: List[Dict[str, str]] = _build_audit_indicators()
ALL_AUDIT_NAME_EN_SET = {i["name_en"] for i in ALL_AUDIT_INDICATORS}
NAME_EN_TO_META = {i["name_en"]: i for i in ALL_AUDIT_INDICATORS}


def _build_area_audit_indicators() -> List[Dict[str, str]]:
    items: List[Dict[str, str]] = []
    seen_en: set = set()
    for group in AREA_INDICATOR_CATALOG_GROUPS:
        for name_zh in group["indicators"]:
            name_en = AREA_INDIMAP.get(name_zh)
            if not name_en or name_en in seen_en:
                continue
            seen_en.add(name_en)
            items.append({
                "name_zh": name_zh,
                "name_en": name_en,
                "group": group["code"],
            })
    return items


ALL_AREA_AUDIT_INDICATORS: List[Dict[str, str]] = _build_area_audit_indicators()
ALL_AREA_AUDIT_NAME_EN_SET = {i["name_en"] for i in ALL_AREA_AUDIT_INDICATORS}


def get_available_area_years() -> List[int]:
    current = timezone.now().year
    years = set(range(current - 20, current + 1))
    years.update(
        y for y in IndicatorArea.objects.values_list("year", flat=True).distinct() if y
    )
    return sorted(years, reverse=True)


def get_default_area_audit_year() -> int:
    row = (
        IndicatorArea.objects.values("year")
        .annotate(cnt=Count("id"))
        .order_by("-cnt", "-year")
        .first()
    )
    if row and row.get("year"):
        return int(row["year"])
    years = get_available_area_years()
    return years[0] if years else timezone.now().year


def get_area_year_record_counts() -> Dict[int, int]:
    return {
        int(row["year"]): row["cnt"]
        for row in IndicatorArea.objects.values("year").annotate(cnt=Count("id"))
        if row.get("year")
    }


def _resolve_area_years(year_param: Optional[str]) -> List[int]:
    if year_param:
        return [int(year_param)]
    return [get_default_area_audit_year()]


def _resolve_city_areas(city_name: str) -> List[str]:
    areas = html_area_Map.get(city_name)
    if areas is None:
        if city_name.endswith("市"):
            areas = html_area_Map.get(city_name.replace("市", ""))
        else:
            areas = html_area_Map.get(f"{city_name}市")
    return list(areas or [])


def _build_area_slots(
    cities: List[dict],
    area_filter: Optional[str] = None,
) -> List[dict]:
    slots = []
    for city_info in cities:
        areas = _resolve_city_areas(city_info["city"])
        for area_name in areas:
            if area_filter and area_name != area_filter:
                continue
            slots.append({
                "city_id": city_info["city_id"],
                "city": city_info["city"],
                "province": city_info["province"],
                "area": area_name,
            })
    return slots


def _resolve_years(year_param: Optional[str]) -> List[int]:
    if year_param:
        return [int(year_param)]
    return [get_default_coverage_year()]


def _get_area_indicators_in_scope(
    group: Optional[str] = None,
    indicator_names: Optional[List[str]] = None,
) -> List[Dict[str, str]]:
    if indicator_names:
        name_set = set(indicator_names)
        return [i for i in ALL_AREA_AUDIT_INDICATORS if i["name_zh"] in name_set]
    if group:
        return [i for i in ALL_AREA_AUDIT_INDICATORS if i["group"] == group]
    return ALL_AREA_AUDIT_INDICATORS


def _load_area_existing_map(
    years: List[int],
    city_ids: List[int],
    indicator_ens: set,
    area_filter: Optional[str] = None,
) -> Dict[Tuple[int, str, str, int], dict]:
    if not city_ids or not indicator_ens:
        return {}

    qs = IndicatorArea.objects.filter(
        year__in=years,
        city_id__in=city_ids,
        name_en__in=indicator_ens,
    )
    if area_filter:
        qs = qs.filter(area=area_filter)

    rows = qs.values(
        "year", "city_id", "area", "name_en", "name_zh",
        "value", "source", "note", "input_method",
    )
    return {
        (row["city_id"], row["area"], row["name_en"], row["year"]): row
        for row in rows
    }


def _build_area_record(
    slot: dict,
    indicator: dict,
    year: int,
    existing: Optional[dict],
) -> dict:
    city_name = slot["city"]
    area_name = slot["area"]
    name_zh = indicator["name_zh"]
    record_id = f"{city_name}_{area_name}_{name_zh}_{year}"
    unit = AREA_INDIMAP_UNIT.get(indicator["name_en"], {}).get("unit", "") or ""

    source_code = normalize_data_source(existing.get("source") if existing else "")
    input_method = (existing.get("input_method") if existing else "") or ""

    if existing:
        return {
            "id": record_id,
            "city": city_name,
            "area": area_name,
            "indicator": existing.get("name_zh") or name_zh,
            "year": year,
            "value": _format_value(existing.get("value")),
            "unit": unit,
            "status": "imported",
            "input_method": input_method,
            "input_method_display": get_input_method_display(input_method) or "—",
            "source": source_code,
            "source_display": get_source_display(
                source_code,
                city=city_name,
                province=slot.get("province", ""),
            ) or "—",
            "remark": existing.get("note") or "",
            "group": indicator["group"],
        }

    return {
        "id": record_id,
        "city": city_name,
        "area": area_name,
        "indicator": name_zh,
        "year": year,
        "value": None,
        "unit": unit,
        "status": "missing",
        "input_method": "",
        "input_method_display": "",
        "source": "",
        "source_display": "",
        "remark": "暂无数据",
        "group": indicator["group"],
    }


def _compute_area_group_stats(
    slots: List[dict],
    indicators: List[dict],
    years: List[int],
    existing_map: Dict[Tuple[int, str, str, int], dict],
) -> Dict[str, dict]:
    stats: Dict[str, dict] = {}
    for group_key, group_name in get_area_group_name_map().items():
        group_inds = [i for i in indicators if i["group"] == group_key]
        if not group_inds:
            continue
        total = len(slots) * len(group_inds) * len(years)
        imported = 0
        for slot in slots:
            for item in group_inds:
                for year in years:
                    key = (slot["city_id"], slot["area"], item["name_en"], year)
                    if key in existing_map:
                        imported += 1
        stats[group_key] = {
            "name": group_name,
            "total": total,
            "imported": imported,
            "rate": round(imported / total * 100, 1) if total > 0 else 0.0,
        }
    return stats


def get_area_indicator_audit_data(
    year_param: Optional[str] = None,
    province: Optional[str] = None,
    city: Optional[str] = None,
    area: Optional[str] = None,
    group: Optional[str] = None,
    indicator_names: Optional[List[str]] = None,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
) -> Dict:
    years = _resolve_area_years(year_param)
    cities = get_cities_in_scope(province, city)
    indicators = _get_area_indicators_in_scope(group, indicator_names)
    indicator_ens = {i["name_en"] for i in indicators}
    city_ids = [c["city_id"] for c in cities]
    slots = _build_area_slots(cities, area_filter=area)

    existing_map = _load_area_existing_map(
        years, city_ids, indicator_ens, area_filter=area,
    )

    total_slots = len(slots) * len(indicators) * len(years)
    imported_count = sum(
        1
        for slot in slots
        for item in indicators
        for year in years
        if (slot["city_id"], slot["area"], item["name_en"], year) in existing_map
    )
    summary = _compute_summary(total_slots, imported_count)
    group_stats = _compute_area_group_stats(slots, indicators, years, existing_map)

    start = (page - 1) * page_size
    records = []
    matched_total = 0

    for slot in slots:
        for item in indicators:
            for year in years:
                key = (slot["city_id"], slot["area"], item["name_en"], year)
                existing = existing_map.get(key)
                record_status = "imported" if existing else "missing"

                if status and record_status != status:
                    continue

                matched_total += 1
                if matched_total > start and len(records) < page_size:
                    records.append(_build_area_record(slot, item, year, existing))

    display_total = matched_total if status else total_slots
    total_pages = (display_total + page_size - 1) // page_size if page_size else 1

    if status:
        display_summary = _compute_summary(
            matched_total,
            matched_total if status == "imported" else 0,
        )
    else:
        display_summary = summary

    return {
        "scope": "area",
        "years": years,
        "records": records,
        "total": display_total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "summary": display_summary,
        "group_stats": group_stats,
    }


def _get_indicators_in_scope(
    group: Optional[str] = None,
    indicator_names: Optional[List[str]] = None,
) -> List[Dict[str, str]]:
    if indicator_names:
        name_set = set(indicator_names)
        return [i for i in ALL_AUDIT_INDICATORS if i["name_zh"] in name_set]
    if group:
        return [i for i in ALL_AUDIT_INDICATORS if i["group"] == group]
    return ALL_AUDIT_INDICATORS


def _load_existing_map(
    years: List[int],
    city_ids: List[int],
    indicator_ens: set,
) -> Dict[Tuple[int, str, int], dict]:
    if not city_ids or not indicator_ens:
        return {}

    rows = Indicator.objects.filter(
        year__in=years,
        city_id__in=city_ids,
        name_en__in=indicator_ens,
    ).values("year", "city_id", "name_en", "name_zh", "value", "source", "note", "input_method")

    return {
        (row["city_id"], row["name_en"], row["year"]): row
        for row in rows
    }


def _format_value(value) -> Optional[float]:
    if value is None or value == "":
        return None
    if isinstance(value, Decimal):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _build_record(city_info: dict, indicator: dict, year: int, existing: Optional[dict]) -> dict:
    city_name = city_info["city"]
    name_zh = indicator["name_zh"]
    record_id = f"{city_name}_{name_zh}_{year}"
    unit = INDIMAP_UNIT.get(indicator["name_en"], {}).get("unit", "") or ""

    source_code = normalize_data_source(existing.get("source") if existing else "")
    input_method = (existing.get("input_method") if existing else "") or ""

    if existing:
        return {
            "id": record_id,
            "city": city_name,
            "indicator": existing.get("name_zh") or name_zh,
            "year": year,
            "value": _format_value(existing.get("value")),
            "unit": unit,
            "status": "imported",
            "input_method": input_method,
            "input_method_display": get_input_method_display(input_method) or "—",
            "source": source_code,
            "source_display": get_source_display(
                source_code,
                city=city_name,
                province=city_info.get("province", ""),
            ) or "—",
            "remark": existing.get("note") or "",
            "group": indicator["group"],
        }

    return {
        "id": record_id,
        "city": city_name,
        "indicator": name_zh,
        "year": year,
        "value": None,
        "unit": unit,
        "status": "missing",
        "input_method": "",
        "input_method_display": "",
        "source": "",
        "source_display": "",
        "remark": "暂无数据",
        "group": indicator["group"],
    }


def _compute_summary(total: int, imported: int) -> Dict:
    missing = total - imported
    coverage_rate = round(imported / total * 100, 1) if total > 0 else 0.0
    return {
        "total": total,
        "imported": imported,
        "missing": missing,
        "coverage_rate": coverage_rate,
    }


def _compute_group_stats(
    cities: List[dict],
    indicators: List[dict],
    years: List[int],
    existing_map: Dict[Tuple[int, str, int], dict],
) -> Dict[str, dict]:
    stats: Dict[str, dict] = {}
    for group_key, group_name in get_group_name_map().items():
        group_inds = [i for i in indicators if i["group"] == group_key]
        if not group_inds:
            continue
        total = len(cities) * len(group_inds) * len(years)
        imported = 0
        for city_info in cities:
            for item in group_inds:
                for year in years:
                    if (city_info["city_id"], item["name_en"], year) in existing_map:
                        imported += 1
        stats[group_key] = {
            "name": group_name,
            "total": total,
            "imported": imported,
            "rate": round(imported / total * 100, 1) if total > 0 else 0.0,
        }
    return stats


def get_indicator_audit_data(
    year_param: Optional[str] = None,
    province: Optional[str] = None,
    city: Optional[str] = None,
    group: Optional[str] = None,
    indicator_names: Optional[List[str]] = None,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
) -> Dict:
    years = _resolve_years(year_param)
    cities = get_cities_in_scope(province, city)
    indicators = _get_indicators_in_scope(group, indicator_names)
    indicator_ens = {i["name_en"] for i in indicators}
    city_ids = [c["city_id"] for c in cities]

    existing_map = _load_existing_map(years, city_ids, indicator_ens)

    total_slots = len(cities) * len(indicators) * len(years)
    imported_count = sum(
        1
        for city_info in cities
        for item in indicators
        for year in years
        if (city_info["city_id"], item["name_en"], year) in existing_map
    )
    summary = _compute_summary(total_slots, imported_count)
    group_stats = _compute_group_stats(cities, indicators, years, existing_map)

    # 分页遍历，按状态筛选
    start = (page - 1) * page_size
    records = []
    matched_total = 0

    for city_info in cities:
        for item in indicators:
            for year in years:
                key = (city_info["city_id"], item["name_en"], year)
                existing = existing_map.get(key)
                record_status = "imported" if existing else "missing"

                if status and record_status != status:
                    continue

                matched_total += 1
                if matched_total > start and len(records) < page_size:
                    records.append(_build_record(city_info, item, year, existing))

    display_total = matched_total if status else total_slots
    total_pages = (display_total + page_size - 1) // page_size if page_size else 1

    if status:
        display_summary = _compute_summary(
            matched_total,
            matched_total if status == "imported" else 0,
        )
    else:
        display_summary = summary

    return {
        "scope": "city",
        "years": years,
        "records": records,
        "total": display_total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "summary": display_summary,
        "group_stats": group_stats,
    }
