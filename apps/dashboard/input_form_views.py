import json
import logging

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from apps.coredata.services.input_form_service import (
    get_area_input_form_data,
    get_city_input_form_data,
)

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["GET"])
def input_form_data_api(request):
    """
    手工录入页加载已保存数据（含 Excel 导入）。
    GET params:
      scope: city | area
      year: 年份
      cities: 逗号分隔城市名（scope=city）
      indicators: 逗号分隔指标显示名（含单位）
      areas: scope=area 时 JSON 数组 [{"city":"北京市","area":"朝阳区"},...]
    """
    try:
        scope = request.GET.get("scope", "city")
        year_raw = (request.GET.get("year") or "").strip()
        year = int(year_raw) if year_raw.isdigit() else None
        if not year:
            return JsonResponse({"success": False, "message": "请选择年份"}, status=400)

        indicators = [
            s.strip()
            for s in (request.GET.get("indicators") or "").split(",")
            if s.strip()
        ]
        if not indicators:
            return JsonResponse({"success": True, "data": {}})

        if scope == "area":
            areas_raw = request.GET.get("areas") or "[]"
            try:
                area_items = json.loads(areas_raw)
            except json.JSONDecodeError:
                return JsonResponse({"success": False, "message": "areas 参数格式错误"}, status=400)
            if not isinstance(area_items, list):
                area_items = []
            data = get_area_input_form_data(year, area_items, indicators)
        else:
            cities = [
                s.strip()
                for s in (request.GET.get("cities") or "").split(",")
                if s.strip()
            ]
            if not cities:
                return JsonResponse({"success": True, "data": {}})
            data = get_city_input_form_data(year, cities, indicators)

        return JsonResponse({"success": True, "data": data})
    except Exception as e:
        logger.error("input_form_data_api failed: %s", e)
        return JsonResponse({"success": False, "message": str(e)}, status=500)
