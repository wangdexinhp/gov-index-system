import json
from datetime import timedelta

from django.utils import timezone


DURATION_MAP = {
    "day": ("day", 1, "日会员"),
    "week": ("week", 7, "周会员"),
    "month": ("month", 30, "月会员"),
    "year": ("year", 365, "年会员"),
}


def apply_membership(user, duration: str, cities: list, indicators: list) -> dict:
    """支付成功后写入用户会员权限。"""
    if duration not in DURATION_MAP:
        raise ValueError(f"不支持的会员时长: {duration}")

    level_code, days, level_name = DURATION_MAP[duration]
    profile = user.profile
    now = timezone.now()

    if profile.is_membership_active and profile.membership_expires_at > now:
        new_expiry = profile.membership_expires_at + timedelta(days=days)
    else:
        new_expiry = now + timedelta(days=days)

    profile.membership_level = level_code
    profile.membership_expires_at = new_expiry
    profile.membership_scope_city = json.dumps(cities or [], ensure_ascii=False)
    profile.membership_scope_item = json.dumps(indicators or [], ensure_ascii=False)
    profile.save()

    return {
        "membership_level": level_code,
        "membership_level_name": level_name,
        "expires_at": new_expiry.strftime("%Y-%m-%d %H:%M:%S"),
        "cities": cities,
        "indicators": indicators,
    }
