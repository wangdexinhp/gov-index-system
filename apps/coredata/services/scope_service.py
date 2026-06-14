"""
权限地域展开与城市名校验。
购买时把省/地区/直辖市/市 统一展开为标准城市全名，与查询 API 传参一致。
"""
from typing import Iterable, List, Set

from apps.coredata.management.commands.import_china_regions import CHINA_REGIONS, html_city_Map

# 与购买页 regionList 保持一致
REGION_PROVINCES = {
    "region_northeast": ["辽宁省", "吉林省", "黑龙江省"],
    "region_north": ["北京市", "天津市", "河北省", "山西省", "内蒙古自治区"],
    "region_east": ["上海市", "江苏省", "浙江省", "安徽省", "福建省", "江西省", "山东省"],
    "region_central": ["河南省", "湖北省", "湖南省"],
    "region_south": ["广东省", "广西壮族自治区", "海南省"],
    "region_southwest": ["重庆市", "四川省", "贵州省", "云南省", "西藏自治区"],
    "region_northwest": ["陕西省", "甘肃省", "青海省", "宁夏回族自治区", "新疆维吾尔自治区"],
}

REGION_NAME_TO_ID = {
    "东北地区": "region_northeast",
    "华北地区": "region_north",
    "华东地区": "region_east",
    "华中地区": "region_central",
    "华南地区": "region_south",
    "西南地区": "region_southwest",
    "西北地区": "region_northwest",
}

_SHORT_PROVINCE_MAP = None


def _build_short_province_map() -> dict:
    mapping = {}
    for prov in CHINA_REGIONS:
        full = prov["province_name"]
        short = full.replace("省", "").replace("市", "").replace("自治区", "").replace("壮族", "").replace("回族", "").replace("维吾尔", "")
        mapping[short] = full
        mapping[full] = full
        if full.endswith("市"):
            mapping[full[:-1]] = full
    for key in html_city_Map:
        mapping[key] = key
        if key.endswith("省"):
            mapping[key[:-1]] = key
        elif key.endswith("市") and key in ("北京市", "天津市", "上海市", "重庆市"):
            mapping[key[:-1]] = key
        elif "自治区" in key or "特别行政区" in key:
            short = key.replace("壮族", "").replace("回族", "").replace("维吾尔", "").replace("自治区", "").replace("特别行政区", "")
            mapping[short] = key
    return mapping


def _short_map() -> dict:
    global _SHORT_PROVINCE_MAP
    if _SHORT_PROVINCE_MAP is None:
        _SHORT_PROVINCE_MAP = _build_short_province_map()
    return _SHORT_PROVINCE_MAP


def normalize_province_name(name: str) -> str:
    name = (name or "").strip()
    if not name:
        return name
    return _short_map().get(name, name)


def normalize_city_name(name: str) -> str:
    name = (name or "").strip()
    if not name:
        return name
    if name == "全国":
        return name
    if name.endswith("市") or name.endswith("盟") or name.endswith("州") or name.endswith("地区"):
        return name
    if name in ("香港", "澳门"):
        return name
    return name + "市" if len(name) <= 4 else name


def cities_in_province(province_name: str) -> List[str]:
    key = normalize_province_name(province_name)
    return list(html_city_Map.get(key, []))


def cities_in_region(region_id: str = "", region_name: str = "") -> List[str]:
    rid = region_id or REGION_NAME_TO_ID.get(region_name, "")
    provinces = REGION_PROVINCES.get(rid, [])
    cities: List[str] = []
    for prov in provinces:
        cities.extend(cities_in_province(prov))
    return cities


def expand_scope_to_cities(level_code: str, scope_name: str, scope_id: str = "") -> List[str]:
    scope_name = (scope_name or "").strip()
    if level_code == "national" or scope_name == "全国":
        return ["全国"]

    if level_code in ("city", "municipality"):
        return [normalize_city_name(scope_name)]

    if level_code == "province":
        cities = cities_in_province(scope_name)
        return cities if cities else [normalize_city_name(scope_name)]

    if level_code == "region":
        cities = cities_in_region(scope_id, scope_name)
        return cities if cities else [scope_name]

    return [normalize_city_name(scope_name)]


def expand_order_items_to_cities(items: Iterable) -> List[str]:
    result: Set[str] = set()
    for item in items:
        cities = expand_scope_to_cities(item.level_code, item.scope_name, item.scope_id)
        result.update(cities)
    return sorted(result)


def is_city_allowed(requested_city: str, allowed_cities: List[str]) -> bool:
    if not requested_city:
        return True
    if "全国" in allowed_cities:
        return True
    req = normalize_city_name(requested_city)
    allowed_set = {normalize_city_name(c) for c in allowed_cities}
    if req in allowed_set:
        return True
    # 兼容查询传简称
    if requested_city in allowed_cities:
        return True
    return False
