import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from apps.coredata.services.coverage_service import (
    get_coverage_overview,
    get_missing_records,
    rebuild_coverage_stats,
)


def _require_admin(request):
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "message": "请先登录"}, status=401)
    profile = getattr(request.user, "profile", None)
    if not profile or profile.membership_level != "admin":
        return JsonResponse({"success": False, "message": "需要管理员权限"}, status=403)
    return None


@login_required
@require_http_methods(["GET"])
def coverage_overview_api(request):
    """
    数据覆盖查询主接口
    GET /dashboard/api/coverage-overview/
    参数: year, province, city, indicator_group
    """
    try:
        data = get_coverage_overview(
            year_param=request.GET.get("year") or None,
            province=request.GET.get("province") or None,
            city=request.GET.get("city") or None,
            indicator_group=request.GET.get("indicator_group") or None,
        )
        return JsonResponse({"success": True, **data})
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def missing_records_api(request):
    """
    缺失指标补录清单
    GET /dashboard/api/missing-records/
    参数: year, province, city, indicator, page, page_size
    """
    try:
        page = max(1, int(request.GET.get("page", 1)))
        page_size = min(500, max(1, int(request.GET.get("page_size", 100))))
        data = get_missing_records(
            year_param=request.GET.get("year") or None,
            province=request.GET.get("province") or None,
            city=request.GET.get("city") or None,
            indicator=request.GET.get("indicator") or None,
            page=page,
            page_size=page_size,
        )
        return JsonResponse({"success": True, **data})
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def rebuild_coverage_stats_api(request):
    """
    重建覆盖统计缓存表
    POST /dashboard/api/rebuild-coverage-stats/
    请求体: {"year": 2025}  // year 可选，不传则重建所有有数据的年份
    """
    denied = _require_admin(request)
    if denied:
        return denied
    try:
        body = json.loads(request.body or "{}")
        result = rebuild_coverage_stats(year_param=body.get("year"))
        return JsonResponse({"success": True, **result})
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "请求体 JSON 格式错误"}, status=400)
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)
