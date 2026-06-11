import uuid
from decimal import Decimal
from typing import Dict, List, Tuple

from django.db import transaction
from django.utils import timezone

from apps.coredata.models.order import MembershipOrder, MembershipOrderItem
from apps.coredata.services.pricing_config_service import get_duration_multipliers


LEVEL_NAME_TO_CODE = {
    "全国": "national",
    "地区": "region",
    "省": "province",
    "直辖市": "municipality",
    "市": "city",
}

USER_TYPE_TO_DB = {
    "personal": "personal",
    "organization": "org",
}

DURATION_TO_DB = {
    "year": "year",
    "month": "month",
    "week": "week",
    "day": "24hour",
}


def _resolve_unit_price(level_code: str, user_type: str, duration: str) -> Decimal:
    from apps.coredata.models.price import PricingConfig

    db_user_type = USER_TYPE_TO_DB.get(user_type, user_type)
    db_duration = DURATION_TO_DB.get(duration, duration)

    exact = PricingConfig.objects.filter(
        level_code=level_code,
        user_type=db_user_type,
        duration=db_duration,
        is_active=True,
    ).first()
    if exact:
        return Decimal(str(exact.price))

    year_row = PricingConfig.objects.filter(
        level_code=level_code,
        user_type=db_user_type,
        duration="year",
        is_active=True,
    ).first()
    if not year_row:
        return Decimal("0")

    multipliers = get_duration_multipliers()
    mult_key = duration if duration in multipliers else db_duration
    if mult_key not in multipliers and duration == "day":
        mult_key = "day"
    multiplier = Decimal(str(multipliers.get(mult_key, multipliers.get("month", 0.1))))
    return Decimal(str(year_row.price)) * multiplier


def calculate_order_amount(user_type: str, duration: str, permissions: List[dict]) -> Tuple[Decimal, List[dict]]:
    if not permissions:
        raise ValueError("请至少选择一个权限")

    items = []
    total = Decimal("0")
    for perm in permissions:
        level = perm.get("level") or perm.get("typeName") or ""
        level_code = perm.get("level_code") or LEVEL_NAME_TO_CODE.get(level, "")
        if not level_code:
            raise ValueError(f"无法识别权限级别: {level}")

        unit_price = _resolve_unit_price(level_code, user_type, duration)
        if unit_price <= 0:
            raise ValueError(f"未配置价格: {level} / {user_type} / {duration}")

        total += unit_price
        items.append({
            "level": level,
            "level_code": level_code,
            "scope_name": perm.get("name") or perm.get("scope_name") or level,
            "scope_id": perm.get("id") or perm.get("scope_id") or "",
            "year_price": _resolve_unit_price(level_code, user_type, "year"),
            "final_price": unit_price,
        })
    return total, items


def _generate_order_no() -> str:
    return f"ORD{timezone.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:6].upper()}"


@transaction.atomic
def create_membership_order(user, user_type: str, duration: str, permissions: List[dict]) -> MembershipOrder:
    total, item_rows = calculate_order_amount(user_type, duration, permissions)
    if total <= 0:
        raise ValueError("订单金额无效")

    order = MembershipOrder.objects.create(
        order_no=_generate_order_no(),
        user=user,
        user_type=user_type,
        duration=duration,
        total_amount=total,
        status=MembershipOrder.Status.PENDING,
    )
    for row in item_rows:
        MembershipOrderItem.objects.create(order=order, **row)
    return order


def mark_order_paid(order_no: str, payment_channel: str = "alipay") -> MembershipOrder:
    order = MembershipOrder.objects.select_for_update().filter(order_no=order_no).first()
    if not order:
        raise ValueError("订单不存在")
    if order.status == MembershipOrder.Status.PAID:
        return order
    if order.status != MembershipOrder.Status.PENDING:
        raise ValueError(f"订单状态不可支付: {order.get_status_display()}")

    order.status = MembershipOrder.Status.PAID
    order.paid_at = timezone.now()
    order.payment_channel = payment_channel
    order.save(update_fields=["status", "paid_at", "payment_channel", "updated_at"])
    return order


def build_membership_payload_from_order(order: MembershipOrder) -> Dict:
    cities = [item.scope_name for item in order.items.all()]
    if any(item.level_code == "national" for item in order.items.all()):
        cities = ["全国"] + [c for c in cities if c != "全国"]

    from apps.coredata.services.pricing_config_service import get_indicator_list

    user_type_key = "personal" if order.user_type == "personal" else "org"
    indicators = [row["name"] for row in get_indicator_list(user_type_key)]

    return {
        "duration": order.duration if order.duration != "day" else "day",
        "cities": cities,
        "indicators": indicators,
    }
