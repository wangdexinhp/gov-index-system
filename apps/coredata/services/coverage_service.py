from decimal import Decimal
from typing import Dict, List, Optional

from django.db import DatabaseError
from django.db.models import Count
from django.utils import timezone

from apps.coredata.indicator_catalog import (
    get_area_group_name_map,
    get_area_indicator_group_map,
    get_group_name_map,
    get_indicator_group_map,
)
from apps.coredata.management.commands.import_china_regions import CHINA_REGIONS, html_area_Map
from apps.coredata.management.commands.indicator_zh_en import (
    AREA_INDIMAP as _AREA_INDIMAP,
    AREA_INDIMAP_UNIT as _AREA_INDIMAP_UNIT,
    INDIMAP as _INDIMAP,
    INDIMAP_UNIT as _INDIMAP_UNIT,
)
from apps.coredata.models.indicator import Indicator, IndicatorArea
from apps.coredata.models.stats import CityCompletionStats, IndicatorCoverageStats

# 覆盖统计业务口径：336 个地市级（排除港澳台、省直辖县级市、三沙、儋州）
COVERAGE_EXCLUDED_PROVINCES = frozenset({"台湾省", "香港特别行政区", "澳门特别行政区"})
COVERAGE_EXCLUDED_CITIES = frozenset({
    "仙桃市", "潜江市", "天门市", "神农架林区",
    "石河子市", "阿拉尔市", "图木舒克市", "五家渠市", "铁门关市",
    "三沙市", "儋州市",
})

GROUP_NAMES = get_group_name_map()
AREA_GROUP_NAMES = get_area_group_name_map()

# 不参与覆盖统计的指标（元数据列）
COVERAGE_EXCLUDED_NAME_EN = frozenset({"city_name"})


def _indicator_unit(name_en: str) -> str:
    return (_INDIMAP_UNIT.get(name_en) or {}).get("unit") or ""


def _build_trackable_indicators() -> List[Dict[str, str]]:
    """从指标目录 + INDIMAP 构建可追踪指标列表（不含备注项）。"""
    group_map = get_indicator_group_map()
    seen_en: set = set()
    items: List[Dict[str, str]] = []
    for name_zh, group in group_map.items():
        name_en = _INDIMAP.get(name_zh, "")
        if not name_en or name_en in seen_en or name_en in COVERAGE_EXCLUDED_NAME_EN:
            continue
        seen_en.add(name_en)
        items.append({
            "name_zh": name_zh,
            "name_en": name_en,
            "group": group,
            "unit": _indicator_unit(name_en),
        })
    return items


TRACKABLE_INDICATORS = _build_trackable_indicators()
TRACKABLE_NAME_EN_SET = {item["name_en"] for item in TRACKABLE_INDICATORS}


def _area_indicator_unit(name_en: str) -> str:
    return (_AREA_INDIMAP_UNIT.get(name_en) or {}).get("unit") or ""


def _build_area_trackable_indicators() -> List[Dict[str, str]]:
    group_map = get_area_indicator_group_map()
    seen_en: set = set()
    items: List[Dict[str, str]] = []
    for name_zh, group in group_map.items():
        name_en = _AREA_INDIMAP.get(name_zh, "")
        if not name_en or name_en in seen_en:
            continue
        seen_en.add(name_en)
        items.append({
            "name_zh": name_zh,
            "name_en": name_en,
            "group": group,
            "unit": _area_indicator_unit(name_en),
        })
    return items


AREA_TRACKABLE_INDICATORS = _build_area_trackable_indicators()
AREA_TRACKABLE_NAME_EN_SET = {item["name_en"] for item in AREA_TRACKABLE_INDICATORS}


def get_available_area_years() -> List[int]:
    db_years = sorted({
        y for y in IndicatorArea.objects.values_list("year", flat=True).distinct() if y
    }, reverse=True)
    current = timezone.now().year
    if current not in db_years:
        db_years.append(current)
        db_years.sort(reverse=True)
    return db_years


def get_default_area_coverage_year() -> int:
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


def _resolve_city_areas(city_name: str) -> List[str]:
    areas = html_area_Map.get(city_name)
    if areas is None:
        if city_name.endswith("市"):
            areas = html_area_Map.get(city_name.replace("市", ""))
        else:
            areas = html_area_Map.get(f"{city_name}市")
    return list(areas or [])


def _build_area_slots(
    cities: List[Dict],
    area_filter: Optional[str] = None,
) -> List[Dict]:
    slots = []
    for city_info in cities:
        for area_name in _resolve_city_areas(city_info["city"]):
            if area_filter and area_name != area_filter:
                continue
            slots.append({
                "city_id": city_info["city_id"],
                "city": city_info["city"],
                "province": city_info["province"],
                "area": area_name,
            })
    return slots


def get_available_years() -> List[int]:
    """返回指标库中有数据的年份（降序），并附带当前年份。"""
    db_years = sorted({
        y for y in Indicator.objects.values_list("year", flat=True).distinct() if y
    }, reverse=True)
    current = timezone.now().year
    if current not in db_years:
        db_years.append(current)
        db_years.sort(reverse=True)
    return db_years


def get_default_coverage_year() -> int:
    """默认年份：取指标记录数最多的年份（并列时取较新的年份）。"""
    row = (
        Indicator.objects.values("year")
        .annotate(cnt=Count("id"))
        .order_by("-cnt", "-year")
        .first()
    )
    if row and row.get("year"):
        return int(row["year"])
    years = get_available_years()
    return years[0] if years else timezone.now().year


def get_year_record_counts() -> Dict[int, int]:
    return {
        int(row["year"]): row["cnt"]
        for row in Indicator.objects.values("year").annotate(cnt=Count("id"))
        if row.get("year")
    }


def resolve_year(year_param: Optional[str]) -> int:
    if year_param:
        return int(year_param)
    return get_default_coverage_year()


def _build_city_catalog() -> List[Dict]:
    catalog = []
    for prov in CHINA_REGIONS:
        province_name = prov["province_name"]
        if province_name in COVERAGE_EXCLUDED_PROVINCES:
            continue
        province_code = int(prov["province_code"])
        for city in prov.get("cities", []):
            city_name = city["name"]
            if city_name in COVERAGE_EXCLUDED_CITIES:
                continue
            catalog.append({
                "city_id": int(city["code"]),
                "city": city_name,
                "province_id": province_code,
                "province": province_name,
            })
    return catalog


def get_cities_in_scope(
    province: Optional[str] = None,
    city: Optional[str] = None,
) -> List[Dict]:
    catalog = _build_city_catalog()
    if city:
        city_key = city if city.endswith("市") else f"{city}市"
        return [c for c in catalog if c["city"] == city_key or c["city"].replace("市", "") == city.replace("市", "")]
    if province:
        return [c for c in catalog if c["province"] == province]
    return catalog


def _get_completed_by_city(year: int, city_ids: List[int]) -> Dict[int, set]:
    result: Dict[int, set] = {cid: set() for cid in city_ids}
    if not city_ids:
        return result
    if not Indicator.objects.filter(year=year).exists():
        return result

    rows = Indicator.objects.filter(
        year=year,
        city_id__in=city_ids,
        name_en__in=TRACKABLE_NAME_EN_SET,
    ).values_list("city_id", "name_en")
    for city_id, name_en in rows:
        result.setdefault(city_id, set()).add(name_en)
    return result


def _get_covered_cities_by_indicator(year: int, city_ids: List[int]) -> Dict[str, set]:
    rows = Indicator.objects.filter(
        year=year,
        city_id__in=city_ids,
        name_en__in=TRACKABLE_NAME_EN_SET,
    ).values_list("name_en", "city_id")
    result: Dict[str, set] = {item["name_en"]: set() for item in TRACKABLE_INDICATORS}
    for name_en, city_id in rows:
        result.setdefault(name_en, set()).add(city_id)
    return result


def _calc_rate(completed: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round(completed / total * 100, 1)


def compute_city_completion(
    year: int,
    cities: List[Dict],
    indicator_group: Optional[str] = None,
) -> List[Dict]:
    indicators = TRACKABLE_INDICATORS
    if indicator_group and indicator_group != "all":
        indicators = [i for i in indicators if i["group"] == indicator_group]

    total_indicators = len(indicators)
    indicator_ens = {i["name_en"] for i in indicators}
    city_ids = [c["city_id"] for c in cities]
    completed_map = _get_completed_by_city(year, city_ids)

    result = []
    for city_info in cities:
        completed_set = completed_map.get(city_info["city_id"], set()) & indicator_ens
        completed = len(completed_set)
        rate = _calc_rate(completed, total_indicators)
        result.append({
            "city_id": city_info["city_id"],
            "city": city_info["city"],
            "province": city_info["province"],
            "completed": completed,
            "total": total_indicators,
            "rate": rate,
        })
    result.sort(key=lambda x: (-x["rate"], x["city"]))
    return result


def compute_indicator_coverage(
    year: int,
    cities: List[Dict],
    indicator_group: Optional[str] = None,
) -> List[Dict]:
    indicators = TRACKABLE_INDICATORS
    if indicator_group and indicator_group != "all":
        indicators = [i for i in indicators if i["group"] == indicator_group]

    total_cities = len(cities)
    city_ids = [c["city_id"] for c in cities]
    covered_map = _get_covered_cities_by_indicator(year, city_ids)

    result = []
    for item in indicators:
        covered = len(covered_map.get(item["name_en"], set()))
        rate = _calc_rate(covered, total_cities)
        result.append({
            "indicator": item["name_zh"],
            "indicator_en": item["name_en"],
            "group": item["group"],
            "group_name": GROUP_NAMES.get(item["group"], "其他"),
            "covered": covered,
            "total": total_cities,
            "rate": rate,
        })
    result.sort(key=lambda x: (-x["rate"], x["indicator"]))
    return result


def build_summary(city_completion: List[Dict], indicator_coverage: List[Dict]) -> Dict:
    total_cities = len(city_completion)
    total_indicators = len(indicator_coverage) or len(TRACKABLE_INDICATORS)
    avg_completion = (
        round(sum(c["rate"] for c in city_completion) / total_cities, 1) if total_cities else 0.0
    )
    avg_coverage = (
        round(sum(i["rate"] for i in indicator_coverage) / len(indicator_coverage), 1)
        if indicator_coverage else 0.0
    )
    return {
        "total_cities": total_cities,
        "avg_completion_rate": avg_completion,
        "total_indicators": total_indicators,
        "avg_coverage_rate": avg_coverage,
    }


def _load_cached_overview(year: int) -> Optional[Dict]:
    """读取统计缓存；表不存在或数据异常时返回 None，由实时计算兜底。"""
    try:
        if not CityCompletionStats.objects.filter(year=year).exists():
            return None

        city_stats = CityCompletionStats.objects.filter(year=year).order_by("-completion_rate")
        city_completion = [{
            "city_id": s.city_id,
            "city": s.city_name,
            "province": s.province_name,
            "completed": s.completed_indicators,
            "total": s.total_indicators,
            "rate": float(s.completion_rate),
        } for s in city_stats]

        ind_stats = IndicatorCoverageStats.objects.filter(year=year).order_by("-coverage_rate")
        indicator_coverage = [{
            "indicator": s.indicator_name,
            "indicator_en": s.indicator_name_en,
            "group": s.indicator_group,
            "group_name": GROUP_NAMES.get(s.indicator_group, "其他"),
            "covered": s.covered_cities,
            "total": s.total_cities,
            "rate": float(s.coverage_rate),
        } for s in ind_stats]

        if not city_completion and not indicator_coverage:
            return None

        return {
            "city_completion": city_completion,
            "indicator_coverage": indicator_coverage,
        }
    except DatabaseError:
        return None


def _cache_matches_scope(cached: Dict, cities: List[Dict]) -> bool:
    """缓存与当前地市/指标口径不一致时丢弃，避免仍显示 371 地市等旧数据。"""
    expected_city_ids = {c["city_id"] for c in cities}
    cached_city_ids = {c["city_id"] for c in cached.get("city_completion", [])}
    if cached_city_ids != expected_city_ids:
        return False
    if len(cached.get("indicator_coverage", [])) != len(TRACKABLE_INDICATORS):
        return False
    return True


def get_coverage_overview(
    year_param: Optional[str] = None,
    province: Optional[str] = None,
    city: Optional[str] = None,
    indicator_group: Optional[str] = None,
) -> Dict:
    year = resolve_year(year_param)
    cities = get_cities_in_scope(province, city)

    use_cache = not province and not city and not indicator_group
    cached = _load_cached_overview(year) if use_cache else None
    if cached and not _cache_matches_scope(cached, cities):
        cached = None

    if cached:
        city_completion = cached["city_completion"]
        indicator_coverage = cached["indicator_coverage"]
    else:
        city_completion = compute_city_completion(year, cities, indicator_group)
        indicator_coverage = compute_indicator_coverage(year, cities, indicator_group)

    return {
        "scope": "city",
        "year": year,
        "summary": build_summary(city_completion, indicator_coverage),
        "city_completion": city_completion,
        "indicator_coverage": indicator_coverage,
    }


def get_missing_records(
    year_param: Optional[str] = None,
    province: Optional[str] = None,
    city: Optional[str] = None,
    indicator: Optional[str] = None,
    page: int = 1,
    page_size: int = 100,
) -> Dict:
    year = resolve_year(year_param)
    cities = get_cities_in_scope(province, city)
    indicators = TRACKABLE_INDICATORS
    if indicator:
        indicators = [i for i in indicators if i["name_zh"] == indicator]

    city_ids = [c["city_id"] for c in cities]
    completed_map = _get_completed_by_city(year, city_ids)
    indicator_ens = {item["name_en"] for item in indicators}

    completed_count = 0
    for city_info in cities:
        completed_set = completed_map.get(city_info["city_id"], set())
        completed_count += len(completed_set & indicator_ens)

    total = len(cities) * len(indicators) - completed_count
    start = (page - 1) * page_size
    page_data = []
    cursor = 0

    for city_info in cities:
        completed_set = completed_map.get(city_info["city_id"], set())
        for item in indicators:
            if item["name_en"] in completed_set:
                continue
            if cursor >= start and len(page_data) < page_size:
                page_data.append({
                    "id": f"{city_info['city']}_{item['name_zh']}_{year}",
                    "city": city_info["city"],
                    "city_id": city_info["city_id"],
                    "province": city_info["province"],
                    "indicator": item["name_zh"],
                    "indicator_en": item["name_en"],
                    "unit": item.get("unit") or "",
                    "year": year,
                    "group": item["group"],
                })
            cursor += 1
            if len(page_data) >= page_size:
                break
        if len(page_data) >= page_size:
            break

    return {
        "scope": "city",
        "year": year,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if page_size else 1,
        "data": page_data,
    }


def _get_completed_by_area_slot(
    year: int,
    city_ids: List[int],
) -> Dict[tuple, set]:
    result: Dict[tuple, set] = {}
    if not city_ids:
        return result
    rows = IndicatorArea.objects.filter(
        year=year,
        city_id__in=city_ids,
        name_en__in=AREA_TRACKABLE_NAME_EN_SET,
    ).values_list("city_id", "area", "name_en")
    for city_id, area, name_en in rows:
        result.setdefault((city_id, area), set()).add(name_en)
    return result


def compute_area_completion(
    year: int,
    slots: List[Dict],
    indicator_group: Optional[str] = None,
) -> List[Dict]:
    indicators = AREA_TRACKABLE_INDICATORS
    if indicator_group and indicator_group != "all":
        indicators = [i for i in indicators if i["group"] == indicator_group]

    total_indicators = len(indicators)
    indicator_ens = {i["name_en"] for i in indicators}
    city_ids = list({s["city_id"] for s in slots})
    completed_map = _get_completed_by_area_slot(year, city_ids)

    result = []
    for slot in slots:
        completed_set = completed_map.get((slot["city_id"], slot["area"]), set()) & indicator_ens
        completed = len(completed_set)
        rate = _calc_rate(completed, total_indicators)
        result.append({
            "city_id": slot["city_id"],
            "city": slot["city"],
            "area": slot["area"],
            "province": slot["province"],
            "completed": completed,
            "total": total_indicators,
            "rate": rate,
        })
    result.sort(key=lambda x: (-x["rate"], x["city"], x["area"]))
    return result


def compute_area_indicator_coverage(
    year: int,
    slots: List[Dict],
    indicator_group: Optional[str] = None,
) -> List[Dict]:
    indicators = AREA_TRACKABLE_INDICATORS
    if indicator_group and indicator_group != "all":
        indicators = [i for i in indicators if i["group"] == indicator_group]

    total_slots = len(slots)
    city_ids = list({s["city_id"] for s in slots})
    completed_map = _get_completed_by_area_slot(year, city_ids)
    covered_map: Dict[str, set] = {item["name_en"]: set() for item in indicators}

    for slot in slots:
        completed_set = completed_map.get((slot["city_id"], slot["area"]), set())
        for name_en in completed_set:
            if name_en in covered_map:
                covered_map[name_en].add((slot["city_id"], slot["area"]))

    result = []
    for item in indicators:
        covered = len(covered_map.get(item["name_en"], set()))
        rate = _calc_rate(covered, total_slots)
        result.append({
            "indicator": item["name_zh"],
            "indicator_en": item["name_en"],
            "group": item["group"],
            "group_name": AREA_GROUP_NAMES.get(item["group"], "其他"),
            "covered": covered,
            "total": total_slots,
            "rate": rate,
        })
    result.sort(key=lambda x: (-x["rate"], x["indicator"]))
    return result


def get_area_coverage_overview(
    year_param: Optional[str] = None,
    province: Optional[str] = None,
    city: Optional[str] = None,
    area: Optional[str] = None,
    indicator_group: Optional[str] = None,
) -> Dict:
    year = resolve_year(year_param)
    cities = get_cities_in_scope(province, city)
    slots = _build_area_slots(cities, area_filter=area)
    area_completion = compute_area_completion(year, slots, indicator_group)
    indicator_coverage = compute_area_indicator_coverage(year, slots, indicator_group)
    summary = build_summary(area_completion, indicator_coverage)
    summary["scope"] = "area"
    return {
        "scope": "area",
        "year": year,
        "summary": summary,
        "area_completion": area_completion,
        "indicator_coverage": indicator_coverage,
    }


def get_area_missing_records(
    year_param: Optional[str] = None,
    province: Optional[str] = None,
    city: Optional[str] = None,
    area: Optional[str] = None,
    indicator: Optional[str] = None,
    page: int = 1,
    page_size: int = 100,
) -> Dict:
    year = resolve_year(year_param)
    cities = get_cities_in_scope(province, city)
    slots = _build_area_slots(cities, area_filter=area)
    indicators = AREA_TRACKABLE_INDICATORS
    if indicator:
        indicators = [i for i in indicators if i["name_zh"] == indicator]

    city_ids = list({s["city_id"] for s in slots})
    completed_map = _get_completed_by_area_slot(year, city_ids)
    indicator_ens = {item["name_en"] for item in indicators}

    completed_count = 0
    for slot in slots:
        completed_set = completed_map.get((slot["city_id"], slot["area"]), set())
        completed_count += len(completed_set & indicator_ens)

    total = len(slots) * len(indicators) - completed_count
    start = (page - 1) * page_size
    page_data = []
    cursor = 0

    for slot in slots:
        completed_set = completed_map.get((slot["city_id"], slot["area"]), set())
        for item in indicators:
            if item["name_en"] in completed_set:
                continue
            if cursor >= start and len(page_data) < page_size:
                page_data.append({
                    "id": f"{slot['city']}_{slot['area']}_{item['name_zh']}_{year}",
                    "city": slot["city"],
                    "city_id": slot["city_id"],
                    "area": slot["area"],
                    "province": slot["province"],
                    "indicator": item["name_zh"],
                    "indicator_en": item["name_en"],
                    "unit": item.get("unit") or "",
                    "year": year,
                    "group": item["group"],
                })
            cursor += 1
            if len(page_data) >= page_size:
                break
        if len(page_data) >= page_size:
            break

    return {
        "scope": "area",
        "year": year,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if page_size else 1,
        "data": page_data,
    }


def _resolve_rebuild_years(
    year_param: Optional[str] = None,
    years: Optional[List[int]] = None,
) -> List[int]:
    if years:
        return sorted({int(y) for y in years if y}, reverse=True)
    if year_param:
        return [int(year_param)]

    return get_available_years()


def rebuild_coverage_stats(
    year_param: Optional[str] = None,
    years: Optional[List[int]] = None,
) -> Dict:
    years = _resolve_rebuild_years(year_param=year_param, years=years)

    all_cities = get_cities_in_scope()
    rebuilt = 0

    for year in years:
        city_completion = compute_city_completion(year, all_cities)
        indicator_coverage = compute_indicator_coverage(year, all_cities)

        CityCompletionStats.objects.filter(year=year).delete()
        IndicatorCoverageStats.objects.filter(year=year).delete()

        CityCompletionStats.objects.bulk_create([
            CityCompletionStats(
                city_id=item["city_id"],
                city_name=item["city"],
                province_id=next((c["province_id"] for c in all_cities if c["city_id"] == item["city_id"]), None),
                province_name=item["province"],
                year=year,
                total_indicators=item["total"],
                completed_indicators=item["completed"],
                completion_rate=Decimal(str(item["rate"])),
            )
            for item in city_completion
        ])

        IndicatorCoverageStats.objects.bulk_create([
            IndicatorCoverageStats(
                indicator_name=item["indicator"],
                indicator_name_en=item["indicator_en"],
                indicator_group=item["group"],
                year=year,
                total_cities=item["total"],
                covered_cities=item["covered"],
                coverage_rate=Decimal(str(item["rate"])),
            )
            for item in indicator_coverage
        ])
        rebuilt += 1

    return {"years": years, "rebuilt_count": rebuilt}
