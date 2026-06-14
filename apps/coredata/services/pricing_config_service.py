"""
定价配置读写：价格、指标权限、时长系数。
供管理端 order_price.html 与公开购买页共用。
"""
from decimal import Decimal
from typing import Dict, List

from django.db import transaction

from apps.coredata.models.price import DurationMultiplierConfig, IndicatorConfig, PricingConfig


def get_pricing_list() -> List[dict]:
    category_map = {
        "national": "national",
        "region": "region",
        "province": "province",
        "municipality": "municipality",
        "city": "city",
    }
    result = []
    for item in PricingConfig.objects.filter(is_active=True).order_by("sort_order"):
        result.append({
            "level": item.level,
            "userType": item.user_type_name,
            "duration": item.duration_name,
            "price": float(item.price),
            "days": item.days,
            "category": category_map.get(item.level_code, item.level_code),
        })
    return result


def update_pricing_list(price_list: List[dict]) -> int:
    duration_map = {
        "年": "year",
        "月": "month",
        "周": "week",
        "15天": "15days",
        "24小时": "24hour",
    }
    user_type_map = {
        "个人用户": "personal",
        "机构用户": "org",
    }
    level_code_map = {
        "national": "national",
        "region": "region",
        "province": "province",
        "municipality": "municipality",
        "city": "city",
    }

    updated_count = 0
    for item in price_list:
        level_code = level_code_map.get(item.get("category", ""))
        user_type = user_type_map.get(item.get("userType", ""))
        duration = duration_map.get(item.get("duration", ""))
        new_price = item.get("price")
        if not level_code or not user_type or not duration or new_price is None:
            continue
        updated_count += PricingConfig.objects.filter(
            level_code=level_code,
            user_type=user_type,
            duration=duration,
        ).update(price=new_price)
    return updated_count


def get_indicator_list(user_type: str) -> List[dict]:
    rows = IndicatorConfig.objects.filter(
        user_type=user_type,
        is_active=True,
    ).order_by("sort_order")
    return [
        {
            "id": row.id,
            "name": row.indicator_name,
            "desc": row.indicator_desc or "",
        }
        for row in rows
    ]


@transaction.atomic
def replace_indicator_list(user_type: str, user_type_name: str, indicators: List[dict]) -> int:
    IndicatorConfig.objects.filter(user_type=user_type).delete()
    created = 0
    for idx, item in enumerate(indicators):
        name = (item.get("name") or item.get("indicator_name") or "").strip()
        if not name:
            continue
        IndicatorConfig.objects.create(
            user_type=user_type,
            user_type_name=user_type_name,
            indicator_name=name,
            indicator_desc=(item.get("desc") or item.get("indicator_desc") or "").strip(),
            sort_order=(idx + 1) * 10,
            is_active=True,
        )
        created += 1
    return created


def get_duration_multipliers() -> Dict[str, float]:
    defaults = {"year": 1.0, "month": 0.1, "week": 0.025}
    rows = DurationMultiplierConfig.objects.filter(is_active=True)
    for row in rows:
        defaults[row.duration_code] = float(row.multiplier)
    return defaults


def update_duration_multipliers(multipliers: Dict[str, float]) -> int:
    updated = 0
    for code, value in multipliers.items():
        if value is None:
            continue
        count = DurationMultiplierConfig.objects.filter(duration_code=code).update(
            multiplier=Decimal(str(value))
        )
        if count == 0:
            name_map = {"year": "年卡", "month": "月卡", "week": "周卡"}
            DurationMultiplierConfig.objects.create(
                duration_code=code,
                duration_name=name_map.get(code, code),
                multiplier=Decimal(str(value)),
                is_active=True,
            )
            updated += 1
        else:
            updated += count
    return updated
