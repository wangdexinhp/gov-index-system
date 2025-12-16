from typing import Iterable

from apps.coredata.models import City, Indicator, CityIndicatorValue


def get_city_multi_indicators(city: City, year: int, indicators: Iterable[Indicator]):
    """
    返回某城市在某年的多个指标值。
    可以给 public/internal 复用。
    """
    return (
        CityIndicatorValue.objects.filter(
            city=city,
            year=year,
            indicator__in=list(indicators),
        )
        .select_related("indicator")
        .order_by("indicator__code")
    )