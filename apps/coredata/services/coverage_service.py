from decimal import Decimal
from typing import Dict, List, Optional

from django.db import DatabaseError
from django.db.models import Max
from django.utils import timezone

from apps.coredata.management.commands.import_china_regions import CHINA_REGIONS
from apps.coredata.models.indicator import Indicator
from apps.coredata.models.stats import CityCompletionStats, IndicatorCoverageStats
from apps.coredata.utils.mapper import get_city_code_to_province

# 与 indic_data_check_2.html 保持一致的指标组映射
INDICATOR_GROUP_MAP: Dict[str, str] = {
    "常住人口数": "population", "城镇人口数": "population", "乡村人口数": "population",
    "户籍人口数": "population", "年末总人口": "population", "年末总户数": "population",
    "15-19岁人口数": "population", "60岁以上人口数": "population", "出生人口性别比": "population",
    "人口出生率": "population", "城镇化率": "population",
    "GDP": "economic_growth", "人均GDP": "economic_growth", "GDP增长率": "economic_growth",
    "固定资产投资总额": "economic_growth", "固定资产投资总额增长率": "economic_growth",
    "全社会消费品零售总额": "economic_growth", "全社会消费品零售总额增长率": "economic_growth",
    "进出口总额": "economic_growth", "进出口总额增长率": "economic_growth",
    "实际利用外资金额": "economic_growth", "实际利用外资金额增长率": "economic_growth",
    "规模以上工业企业增加值": "economic_growth", "第二产业增加值占GDP比重": "economic_growth",
    "第三产业增加值占GDP比重": "economic_growth", "城镇居民人均可支配收入": "economic_growth",
    "一般公共预算收入": "finance", "财政总收入": "finance", "财政总收入增长率": "finance",
    "一般公共预算支出": "finance", "一般公共服务支出": "finance", "科学技术支出": "finance",
    "公共安全支出": "finance", "文化体育传媒支出": "finance", "环保支出": "finance",
    "社会保障和就业支出": "finance", "教育支出": "finance", "医疗卫生支出": "finance",
    "高新技术企业产值": "education_tech", "高新技术企业增加值": "education_tech",
    "专利授权数量": "education_tech", "有效发明专利量": "education_tech",
    "R&D经费": "education_tech", "普通小学在校学生数": "education_tech",
    "普通中学在校学生数": "education_tech", "高中学在校学生数": "education_tech",
    "城镇登记失业率": "employment", "城镇登记失业人员数": "employment",
    "城镇新增就业人数": "employment", "城镇就业人数": "employment",
    "采矿（掘)业就业人员人数": "employment", "制造业就业人员人数": "employment",
    "森林覆盖率": "ecology", "PM2.5": "ecology", "PM10": "ecology",
    "二氧化硫排放总量": "ecology", "工业废水排放总量": "ecology",
    "生活垃圾无害化处理率": "ecology", "园林绿地面积": "ecology",
}

GROUP_NAMES = {
    "population": "人口数据",
    "economic_growth": "经济增长",
    "finance": "财政指标",
    "education_tech": "教育科技",
    "employment": "就业数据",
    "ecology": "生态环保",
    "other": "其他",
}

# 中文名 -> 英文名（与 INDIMAP 对齐的子集）
from apps.coredata.management.commands.indicator_zh_en import INDIMAP as _INDIMAP

# 页面展示名与 INDIMAP 键名不完全一致时的别名
INDICATOR_NAME_ALIASES = {
    "有效发明专利量": "有效发明专利量（发明专利有效量）",
    "第二产业增加值占GDP比重": "第二产业增加值占GDP（增量）比重",
    "第三产业增加值占GDP比重": "第三产业增加值占GDP（增量）比重",
}


def _resolve_name_en(name_zh: str) -> str:
    key = INDICATOR_NAME_ALIASES.get(name_zh, name_zh)
    return _INDIMAP.get(key, "")


TRACKABLE_INDICATORS: List[Dict[str, str]] = []
for _name_zh, _group in INDICATOR_GROUP_MAP.items():
    _name_en = _resolve_name_en(_name_zh)
    if _name_en:
        TRACKABLE_INDICATORS.append({
            "name_zh": _name_zh,
            "name_en": _name_en,
            "group": _group,
        })

TRACKABLE_NAME_EN_SET = {item["name_en"] for item in TRACKABLE_INDICATORS}


def resolve_year(year_param: Optional[str]) -> int:
    if year_param:
        return int(year_param)
    latest = Indicator.objects.aggregate(max_year=Max("year"))["max_year"]
    return latest or timezone.now().year


def _build_city_catalog() -> List[Dict]:
    catalog = []
    code_map = get_city_code_to_province()
    for prov in CHINA_REGIONS:
        province_name = prov["province_name"]
        province_code = int(prov["province_code"])
        for city in prov.get("cities", []):
            city_code = int(city["code"])
            city_name = city["name"]
            catalog.append({
                "city_id": city_code,
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
    total_indicators = len(TRACKABLE_INDICATORS)
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

    if cached:
        city_completion = cached["city_completion"]
        indicator_coverage = cached["indicator_coverage"]
    else:
        city_completion = compute_city_completion(year, cities, indicator_group)
        indicator_coverage = compute_indicator_coverage(year, cities, indicator_group)

    return {
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
                    "year": year,
                    "group": item["group"],
                })
            cursor += 1
            if len(page_data) >= page_size:
                break
        if len(page_data) >= page_size:
            break

    return {
        "year": year,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if page_size else 1,
        "data": page_data,
    }


def rebuild_coverage_stats(year_param: Optional[str] = None) -> Dict:
    if year_param:
        years = [int(year_param)]
    else:
        db_years = Indicator.objects.values_list("year", flat=True).distinct()
        years = sorted({y for y in db_years if y}, reverse=True)
        if not years:
            years = [timezone.now().year]

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
