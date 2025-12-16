from typing import Dict, Any

from apps.coredata.models import City, Indicator, CityIndicatorValue


def compute_computed_indicators_for_city_year(city: City, year: int) -> Dict[str, Any]:
    """
    根据 city + year 已有的录入指标，计算所有“计算型指标”的数值。
    这里先留空或简单实现，后期你把真实公式填进来。
    返回值示例：{"IND_CODE_A": 123.4, "IND_CODE_B": 0.56, ...}
    """
    # TODO: 读取 city 在该年度的录入指标，做计算
    return {}
