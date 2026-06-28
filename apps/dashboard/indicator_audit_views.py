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
from apps.coredata.indicator_catalog import (
    get_area_indicator_catalog_dict,
    get_area_indicator_catalog_groups,
    get_form_indicator_categories,
    get_group_name_map,
    get_indicator_catalog_dict,
    get_indicator_catalog_groups,
    get_indicator_group_map,
    get_indicator_unit_map,
)
from apps.coredata.services.indicator_audit_service import (
    get_area_indicator_audit_data,
    get_area_year_record_counts,
    get_available_area_years,
    get_default_area_audit_year,
    get_indicator_audit_data,
)
from apps.dashboard.coverage_views import api_login_required

logger = logging.getLogger(__name__)


@api_login_required
@require_http_methods(["GET"])
def indicator_audit_years_api(request):
    """指标校验页：可选年份列表。"""
    try:
        scope = (request.GET.get("scope") or "city").strip().lower()
        if scope == "area":
            years = get_available_area_years()
            return JsonResponse({
                "success": True,
                "scope": "area",
                "years": years,
                "default_year": get_default_area_audit_year(),
                "year_counts": get_area_year_record_counts(),
            })
        years = get_available_years()
        return JsonResponse({
            "success": True,
            "scope": "city",
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
def indicator_catalog_api(request):
    """指标分组目录（查询/录入/校验页共用）。"""
    return JsonResponse({
        "success": True,
        "data": get_indicator_catalog_dict(),
        "groups": get_indicator_catalog_groups(),
        "form_categories": get_form_indicator_categories("city"),
        "group_map": get_indicator_group_map(),
        "group_names": get_group_name_map(),
        "unit_map": get_indicator_unit_map("city"),
        "area_data": get_area_indicator_catalog_dict(),
        "area_groups": get_area_indicator_catalog_groups(),
        "area_form_categories": get_form_indicator_categories("area"),
        "area_unit_map": get_indicator_unit_map("area"),
    })


@api_login_required
@require_http_methods(["GET"])
def indicator_audit_groups_api(request):
    """指标校验页：指标组列表。"""
    scope = (request.GET.get("scope") or "city").strip().lower()
    groups = (
        get_area_indicator_catalog_groups()
        if scope == "area"
        else get_indicator_catalog_groups()
    )
    return JsonResponse({
        "success": True,
        "scope": scope,
        "groups": [{"code": g["code"], "name": g["name"]} for g in groups],
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

        scope = (request.GET.get("scope") or "city").strip().lower()
        common_kwargs = dict(
            year_param=request.GET.get("year") or None,
            province=request.GET.get("province") or None,
            city=request.GET.get("city") or None,
            group=request.GET.get("group") or None,
            indicator_names=indicator_names,
            status=request.GET.get("status") or None,
            page=page,
            page_size=page_size,
        )
        if scope == "area":
            data = get_area_indicator_audit_data(
                area=request.GET.get("area") or None,
                **common_kwargs,
            )
        else:
            data = get_indicator_audit_data(**common_kwargs)
        return JsonResponse({"success": True, **data})
    except Exception as e:
        logger.error("check_data_api failed: %s", e)
        traceback.print_exc()
        return JsonResponse({
            "success": False,
            "message": str(e),
            "records": [],
        }, status=500)
