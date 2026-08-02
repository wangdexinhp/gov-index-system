"""关键指标查询页面与 API。"""
from __future__ import annotations

import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from apps.coredata.special_indicator_catalog import (
    get_special_indicator_tree,
    list_level2,
    list_level3,
    query_special_indicators,
)


def _require_admin(request):
    if request.user.profile.membership_level != 'admin':
        return redirect('/')
    return None


@login_required
@require_http_methods(['GET'])
def special_indicator_query_city(request):
    denied = _require_admin(request)
    if denied:
        return denied
    return render(request, 'dashboard/special_indicator_query.html', {
        'scope': 'city',
        'page_title': '关键指标查询（地市）',
        'back_input_url': '/dashboard/',
        'back_input_label': '地市录入',
    })


@login_required
@require_http_methods(['GET'])
def special_indicator_query_area(request):
    denied = _require_admin(request)
    if denied:
        return denied
    return render(request, 'dashboard/special_indicator_query.html', {
        'scope': 'area',
        'page_title': '关键指标查询（区县）',
        'back_input_url': '/dashboard/area_input',
        'back_input_label': '区县录入',
    })


@login_required
@require_http_methods(['GET'])
def special_indicator_tree_api(request):
    """返回一级/二级/三级树；可按一级、二级筛选。"""
    level1 = request.GET.get('level1', '').strip()
    level2 = request.GET.get('level2', '').strip()
    tree = get_special_indicator_tree()
    return JsonResponse({
        'success': True,
        'tree': tree,
        'level1_options': list(tree.keys()),
        'level2_options': list_level2(level1),
        'level3_options': list_level3(level1, level2),
    })


@login_required
@require_http_methods(['GET', 'POST'])
def special_indicator_query_api(request):
    """查询关键指标数值。"""
    if request.method == 'POST':
        try:
            body = json.loads(request.body.decode('utf-8') or '{}')
        except json.JSONDecodeError:
            body = {}
        data = body
    else:
        data = request.GET

    scope = (data.get('scope') or 'city').strip()
    if scope not in ('city', 'area'):
        scope = 'city'

    year_raw = data.get('year')
    year = int(year_raw) if year_raw not in (None, '', '选择年份') else None

    cities = data.get('cities') or data.get('city') or []
    if isinstance(cities, str):
        cities = [x.strip() for x in cities.split(',') if x.strip()]

    areas = data.get('areas') or data.get('area') or []
    if isinstance(areas, str):
        areas = [x.strip() for x in areas.split(',') if x.strip()]

    indicators = data.get('indicators') or data.get('indicator') or []
    if isinstance(indicators, str):
        indicators = [x.strip() for x in indicators.split(',') if x.strip()]

    result = query_special_indicators(
        scope=scope,
        year=year,
        province=(data.get('province') or '').strip(),
        cities=cities,
        areas=areas,
        level1=(data.get('level1') or '').strip(),
        level2=(data.get('level2') or '').strip(),
        indicators=indicators,
    )
    return JsonResponse(result)
