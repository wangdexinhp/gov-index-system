"""
特殊指标目录（一级 / 二级 / 三级）

数据来源：指标表（一级二级三级）.xlsx
查询时将三级指标中文名映射到库内 name_zh / name_en。
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from django.db.models import Q

from apps.coredata.management.commands.indicator_zh_en import (
    AREA_INDIMAP,
    AREA_INDIMAP_UNIT,
    INDIMAP,
    INDIMAP_UNIT,
)
from apps.coredata.models.indicator import Indicator, IndicatorArea
from apps.coredata.management.commands.import_china_regions import CHINA_REGIONS

_TREE_PATH = Path(__file__).with_name('special_indicator_tree.json')

# 表内三级名 → 库内标准中文名（仅保留可靠映射）
SPECIAL_INDICATOR_ALIASES = {
    '规模以上工业增加值': '规模以上工业企业增加值',
    '规模以上工业增加值增长率': '规模以上工业企业增加值增长率',
    '第二产业增加值占GDP比重': '第二产业增加值占GDP（增量）比重',
    '第三产业增加值占GDP比重': '第三产业增加值占GDP（增量）比重',
    '农村居民人均可支配增长率': '农村居民人均可支配收入增长率',
    '亿元GDP安全生产事故死亡率': '亿元GDP生产安全事故死亡率',
    '万人刑事案件立案件数': '刑事案件立案件数',
    '万人刑事案件破案件数': '刑事案件破案件数',
    '十万人调处各类矛盾纠纷件数': '调处各类矛盾纠纷件数',
    '每万人接待群众来信来访人次': '接待群众来信来访人次',
    '水土流失治理面积（率）': '水土流失治理面积',
    'R&D经费占GDP的比重': 'R&D经费与GDP之比',
    '万人卫生技术人员数量': '卫生技术人员数量',
    '万人拥有医疗机构病床数': '医疗机构病床数',
    '十万人专利授权量': '专利授权量',
    '十万人拥有专业艺术表演团体数量': '艺术表演团体',
    '十万人拥有公共体育场馆个数': '体育场馆',
    '人均园林绿地面积': '园林绿地面积',
    '每百人固定宽带互联网用户数': '固定宽带互联网用户数',
}


@lru_cache(maxsize=1)
def get_special_indicator_tree() -> Dict[str, Dict[str, List[str]]]:
    with open(_TREE_PATH, encoding='utf-8') as f:
        return json.load(f)


def list_level1() -> List[str]:
    return list(get_special_indicator_tree().keys())


def list_level2(level1: str = '') -> List[str]:
    tree = get_special_indicator_tree()
    if level1:
        return list(tree.get(level1, {}).keys())
    out: List[str] = []
    for subs in tree.values():
        out.extend(subs.keys())
    return out


def list_level3(level1: str = '', level2: str = '') -> List[str]:
    tree = get_special_indicator_tree()
    if level1 and level2:
        return list(tree.get(level1, {}).get(level2, []))
    if level1:
        out: List[str] = []
        for items in tree.get(level1, {}).values():
            out.extend(items)
        return out
    if level2:
        out = []
        for subs in tree.values():
            if level2 in subs:
                out.extend(subs[level2])
        return out
    out = []
    for subs in tree.values():
        for items in subs.values():
            out.extend(items)
    return out


def _indimap_for_scope(scope: str) -> Dict[str, str]:
    return AREA_INDIMAP if scope == 'area' else INDIMAP


def _unit_map_for_scope(scope: str) -> Dict[str, dict]:
    return AREA_INDIMAP_UNIT if scope == 'area' else INDIMAP_UNIT


def resolve_indicator_keys(name_zh: str, scope: str = 'city') -> Tuple[List[str], List[str]]:
    """返回 (name_zh 候选, name_en 候选)。"""
    indimap = _indimap_for_scope(scope)
    zh_names = {name_zh}
    mapped = SPECIAL_INDICATOR_ALIASES.get(name_zh)
    if mapped:
        zh_names.add(mapped)
    en_names = []
    for zh in zh_names:
        en = indimap.get(zh)
        if en:
            en_names.append(en)
    return list(zh_names), en_names


def _city_name_to_code() -> Dict[str, int]:
    mapping = {}
    for prov in CHINA_REGIONS:
        for city in prov.get('cities', []):
            mapping[city['name']] = int(city['code'])
            mapping[city['name'].replace('市', '')] = int(city['code'])
    return mapping


def _city_code_to_name() -> Dict[int, str]:
    mapping = {}
    for prov in CHINA_REGIONS:
        for city in prov.get('cities', []):
            mapping[int(city['code'])] = city['name']
    return mapping


def _province_name_to_code() -> Dict[str, int]:
    return {prov['name']: int(prov['code']) for prov in CHINA_REGIONS}


def query_special_indicators(
    *,
    scope: str = 'city',
    year: Optional[int] = None,
    province: str = '',
    cities: Optional[List[str]] = None,
    areas: Optional[List[str]] = None,
    level1: str = '',
    level2: str = '',
    indicators: Optional[List[str]] = None,
) -> Dict:
    """
    按特殊指标树查询已录入数值。
    indicators 为空时，取当前一级/二级下全部三级指标。
    """
    selected = [x.strip() for x in (indicators or []) if x and x.strip()]
    if not selected:
        selected = list_level3(level1, level2)
    if not selected:
        return {'success': True, 'rows': [], 'indicators': [], 'message': '未选择指标'}

    city_map = _city_name_to_code()
    city_ids = []
    for name in cities or []:
        code = city_map.get(name) or city_map.get(name.replace('市', ''))
        if code:
            city_ids.append(code)

    if province and not city_ids:
        prov_code = _province_name_to_code().get(province)
        if prov_code:
            for prov in CHINA_REGIONS:
                if int(prov['code']) == prov_code:
                    city_ids = [int(c['code']) for c in prov.get('cities', [])]
                    break

    # 每个特殊指标 → 查询条件
    query_q = Q()
    display_to_keys = {}
    for zh in selected:
        zh_names, en_names = resolve_indicator_keys(zh, scope)
        display_to_keys[zh] = {'name_zh': zh_names, 'name_en': en_names}
        part = Q(name_zh__in=zh_names)
        if en_names:
            part |= Q(name_en__in=en_names)
        query_q |= part

    filters = {}
    if year:
        filters['year'] = int(year)

    code_to_name = _city_code_to_name()
    unit_map = _unit_map_for_scope(scope)
    indimap = _indimap_for_scope(scope)

    if scope == 'area':
        qs = IndicatorArea.objects.filter(**filters).filter(query_q)
        if city_ids:
            qs = qs.filter(city_id__in=city_ids)
        if areas:
            qs = qs.filter(area__in=areas)
        qs = qs.order_by('year', 'city_id', 'area', 'name_zh')
    else:
        qs = Indicator.objects.filter(**filters).filter(query_q)
        if city_ids:
            qs = qs.filter(city_id__in=city_ids)
        if province:
            prov_code = _province_name_to_code().get(province)
            if prov_code:
                qs = qs.filter(province_id=prov_code)
        qs = qs.order_by('year', 'city_id', 'name_zh')

    def match_display_name(ind) -> str:
        for display, keys in display_to_keys.items():
            if ind.name_zh in keys['name_zh'] or ind.name_en in keys['name_en']:
                return display
        return ind.name_zh

    rows = []
    for ind in qs:
        display = match_display_name(ind)
        en = ind.name_en or indimap.get(SPECIAL_INDICATOR_ALIASES.get(display, display), '')
        unit_info = unit_map.get(en) or {}
        city_name = code_to_name.get(ind.city_id, f'未知({ind.city_id})')
        row = {
            'year': ind.year,
            'city': city_name,
            'indicator': display,
            'value': str(ind.value) if ind.value is not None else '',
            'unit': unit_info.get('unit', ''),
            'source': ind.source or '',
            'note': ind.note or '',
            'input_method': getattr(ind, 'input_method', '') or '',
        }
        if scope == 'area':
            row['area'] = ind.area
        rows.append(row)

    return {
        'success': True,
        'scope': scope,
        'indicators': selected,
        'count': len(rows),
        'rows': rows,
    }
