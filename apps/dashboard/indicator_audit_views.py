import logging
import traceback

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from apps.coredata.services.coverage_service import (
    get_available_years,
    get_default_coverage_year,
    get_year_record_counts,
)
from apps.coredata.indicator_sources import get_form_source_choices, get_source_choices
from apps.coredata.services.indicator_audit_service import (
    AUDIT_GROUP_NAMES,
    get_indicator_audit_data,
)
from apps.dashboard.coverage_views import api_login_required

logger = logging.getLogger(__name__)


@api_login_required
@require_http_methods(["GET"])
def indicator_audit_years_api(request):
    """指标校验页：可选年份列表。"""
    try:
        years = get_available_years()
        return JsonResponse({
            "success": True,
            "years": years,
            "default_year": get_default_coverage_year(),
            "year_counts": get_year_record_counts(),
        })
    except Exception as e:
        logger.error("indicator_audit_years_api failed: %s", e)
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@api_login_required
@require_http_methods(["GET"])
def indicator_sources_api(request):
    """指标数据来源代码与中文名称（全量 / 录入表单子集）。"""
    scope = request.GET.get("scope", "all")
    sources = get_form_source_choices() if scope == "form" else get_source_choices()
    return JsonResponse({"success": True, "sources": sources})


@api_login_required
@require_http_methods(["GET"])
def indicator_audit_groups_api(request):
    """指标校验页：指标组列表。"""
    return JsonResponse({
        "success": True,
        "groups": [
            {"code": code, "name": name}
            for code, name in AUDIT_GROUP_NAMES.items()
        ],
    })


@api_login_required
@require_http_methods(["GET"])
def check_data_api(request):
    """
    指标录入核对查询 API
    GET /dashboard/api/check-data/

    参数:
        year, province, city, group, indicators(逗号分隔中文名), status(imported/missing)
        page, page_size
    """
    try:
        page = max(1, int(request.GET.get("page", 1)))
        page_size = min(200, max(1, int(request.GET.get("page_size", 50))))
        indicators_param = request.GET.get("indicators") or ""
        indicator_names = [
            name.strip()
            for name in indicators_param.split(",")
            if name.strip()
        ] or None

        data = get_indicator_audit_data(
            year_param=request.GET.get("year") or None,
            province=request.GET.get("province") or None,
            city=request.GET.get("city") or None,
            group=request.GET.get("group") or None,
            indicator_names=indicator_names,
            status=request.GET.get("status") or None,
            page=page,
            page_size=page_size,
        )
        return JsonResponse({"success": True, **data})
    except Exception as e:
        logger.error("check_data_api failed: %s", e)
        traceback.print_exc()
        return JsonResponse({
            "success": False,
            "message": str(e),
            "records": [],
        }, status=500)
