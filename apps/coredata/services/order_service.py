import logging
import uuid
from datetime import timedelta
from decimal import Decimal
from typing import Dict, List, Tuple

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.coredata.models.order import MembershipOrder, MembershipOrderItem
from apps.coredata.services.pricing_config_service import get_duration_multipliers
from apps.coredata.services.scope_service import expand_order_items_to_cities

logger = logging.getLogger(__name__)


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

    timeout_minutes = int(getattr(settings, "ORDER_PAY_TIMEOUT_MINUTES", 30))
    order = MembershipOrder.objects.create(
        order_no=_generate_order_no(),
        user=user,
        user_type=user_type,
        duration=duration,
        total_amount=total,
        status=MembershipOrder.Status.PENDING,
        expire_at=timezone.now() + timedelta(minutes=timeout_minutes),
    )
    for row in item_rows:
        MembershipOrderItem.objects.create(order=order, **row)
    return order


def mark_order_paid(
    order_no: str,
    payment_channel: str = "alipay",
    alipay_trade_no: str = "",
) -> MembershipOrder:
    order = MembershipOrder.objects.select_for_update().filter(order_no=order_no).first()
    if not order:
        raise ValueError("订单不存在")
    if order.status == MembershipOrder.Status.PAID:
        return order
    if order.status != MembershipOrder.Status.PENDING:
        raise ValueError(f"订单状态不可支付: {order.get_status_display()}")
    if order.expire_at and timezone.now() > order.expire_at:
        order.status = MembershipOrder.Status.EXPIRED
        order.save(update_fields=["status", "updated_at"])
        raise ValueError("订单已超时")

    order.status = MembershipOrder.Status.PAID
    order.paid_at = timezone.now()
    order.payment_channel = payment_channel
    if alipay_trade_no:
        order.alipay_trade_no = alipay_trade_no
    order.save(update_fields=["status", "paid_at", "payment_channel", "alipay_trade_no", "updated_at"])
    return order


def expire_pending_orders() -> int:
    now = timezone.now()
    qs = MembershipOrder.objects.filter(
        status=MembershipOrder.Status.PENDING,
        expire_at__lt=now,
    )
    return qs.update(status=MembershipOrder.Status.EXPIRED)


def build_membership_payload_from_order(order: MembershipOrder) -> Dict:
    cities = expand_order_items_to_cities(order.items.all())

    from apps.coredata.services.pricing_config_service import get_indicator_list

    user_type_key = "personal" if order.user_type == "personal" else "org"
    indicators = [row["name"] for row in get_indicator_list(user_type_key)]

    return {
        "duration": order.duration if order.duration != "day" else "day",
        "cities": cities,
        "indicators": indicators,
    }


def fulfill_paid_order(order_no: str, payment_channel: str = "alipay", alipay_trade_no: str = "") -> dict:
    """支付成功后标记订单并开通会员（幂等）。

    机构订单在开通权限前二次校验 is_org_verified：
    - 已付款一律先记为 paid（钱已到账）
    - 若认证已失效/未通过，则不开通权限并抛出 ValueError，便于日志与人工处理
    """
    from apps.accounts.models import UserProfile
    from apps.coredata.services.membership_service import apply_membership

    with transaction.atomic():
        order = MembershipOrder.objects.select_for_update().filter(order_no=order_no).first()
        if not order:
            raise ValueError("订单不存在")
        if order.status == MembershipOrder.Status.PAID:
            return {"already_fulfilled": True, "order_no": order_no}

        order = mark_order_paid(order_no, payment_channel=payment_channel, alipay_trade_no=alipay_trade_no)

        if order.user_type in ("organization", "org"):
            profile, _ = UserProfile.objects.select_for_update().get_or_create(user=order.user)
            if not profile.is_org_verified:
                logger.error(
                    "Org order paid but not verified, skip membership order=%s user_id=%s status=%s",
                    order_no,
                    order.user_id,
                    profile.org_verify_status,
                )
                raise ValueError(
                    "机构认证已失效或未通过，订单已支付但未开通权限，请联系客服处理"
                )

        payload = build_membership_payload_from_order(order)
        result = apply_membership(order.user, **payload)
    return result


def get_order_status_for_user(order_no: str, user) -> dict:
    order = MembershipOrder.objects.filter(order_no=order_no, user=user).first()
    if not order:
        raise ValueError("订单不存在")
    if order.status == MembershipOrder.Status.PENDING and order.expire_at and timezone.now() > order.expire_at:
        order.status = MembershipOrder.Status.EXPIRED
        order.save(update_fields=["status", "updated_at"])
    return {
        "order_no": order.order_no,
        "status": order.status,
        "total_amount": float(order.total_amount),
        "expire_at": order.expire_at.isoformat() if order.expire_at else None,
        "paid_at": order.paid_at.isoformat() if order.paid_at else None,
    }
