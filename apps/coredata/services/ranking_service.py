from typing import List

from django.db.models import QuerySet

from apps.coredata.models import City, CityIndicatorValue, Indicator


def rank_cities_by_indicator(year: int, indicator: Indicator, province=None) -> QuerySet[CityIndicatorValue]:
    """
    按某个指标在某年对城市排序。
    province 可选：如果传入，只排这个省内的城市。
    暂时返回 QuerySet，后面你可以封装成专门的 DTO。
    """
    qs = CityIndicatorValue.objects.filter(
        year=year,
        indicator=indicator,
    ).select_related("city", "city__province")

    if province is not None:
        qs = qs.filter(city__province=province)

    # 默认按 value 降序（高分在前）
    return qs.order_by("-value")
