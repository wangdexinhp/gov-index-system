"""
微信支付 Native（扫码）封装：alipay 电脑网站支付的并行渠道。
使用 APIv3（wechatpayv3），返回 code_url 供前端展示二维码。
"""
from __future__ import annotations

import json
import logging
from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


def _resolve_path(path_value: str) -> Path | None:
    raw = (path_value or "").strip()
    if not raw:
        return None
    path = Path(raw)
    if not path.is_absolute():
        path = Path(settings.BASE_DIR) / path
    return path


def _load_private_key() -> str:
    path = _resolve_path(getattr(settings, "WECHAT_PRIVATE_KEY_PATH", "") or "")
    if path is not None and path.is_file():
        return path.read_text(encoding="utf-8").strip()
    content = (getattr(settings, "WECHAT_PRIVATE_KEY", "") or "").strip()
    if content:
        return content
    raise FileNotFoundError(
        "微信商户 API 私钥未配置：请设置 WECHAT_PRIVATE_KEY_PATH 或 WECHAT_PRIVATE_KEY"
    )


def is_wechat_mock_mode() -> bool:
    if getattr(settings, "WECHAT_MOCK", False):
        return True
    mch_id = (getattr(settings, "WECHAT_MCH_ID", "") or "").strip()
    app_id = (getattr(settings, "WECHAT_APP_ID", "") or "").strip()
    return not mch_id or not app_id or mch_id.startswith("mock_")


def _amount_to_fen(total_amount: Decimal) -> int:
    fen = (Decimal(total_amount) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    value = int(fen)
    if value <= 0:
        raise ValueError("微信支付金额无效")
    return value


def _time_expire_rfc3339() -> str:
    minutes = int(getattr(settings, "ORDER_PAY_TIMEOUT_MINUTES", 30))
    expire_at = timezone.now() + timedelta(minutes=minutes)
    # 微信要求带时区偏移，如 2018-06-08T10:34:56+08:00
    local = expire_at.astimezone(timezone.get_current_timezone())
    offset = local.strftime("%z")  # +0800
    if len(offset) == 5:
        offset = f"{offset[:3]}:{offset[3:]}"
    return local.strftime("%Y-%m-%dT%H:%M:%S") + offset


def get_wechat_client():
    if is_wechat_mock_mode():
        return None

    from wechatpayv3 import WeChatPay, WeChatPayType

    cert_dir = _resolve_path(getattr(settings, "WECHAT_CERT_DIR", "") or "certs/wechat")
    if cert_dir is not None:
        cert_dir.mkdir(parents=True, exist_ok=True)

    return WeChatPay(
        wechatpay_type=WeChatPayType.NATIVE,
        mchid=str(settings.WECHAT_MCH_ID),
        private_key=_load_private_key(),
        cert_serial_no=str(settings.WECHAT_CERT_SERIAL_NO),
        apiv3_key=str(settings.WECHAT_API_V3_KEY),
        appid=str(settings.WECHAT_APP_ID),
        notify_url=settings.WECHAT_NOTIFY_URL,
        cert_dir=str(cert_dir) if cert_dir else None,
        logger=logger,
    )


def create_native_payment(order_no: str, total_amount: Decimal, subject: str) -> dict:
    """
    Native 下单，返回 code_url（用于生成二维码）。
    """
    if is_wechat_mock_mode():
        code_url = f"weixin://wxpay/bizpayurl?mock=1&order={order_no}"
        logger.info("WeChat MOCK native pay order=%s amount=%s", order_no, total_amount)
        return {"code_url": code_url, "mock": True}

    from wechatpayv3 import WeChatPayType

    client = get_wechat_client()
    if not client:
        raise RuntimeError("微信支付客户端未配置")

    code, message = client.pay(
        description=(subject or "城策智库权限")[:127],
        out_trade_no=order_no,
        amount={"total": _amount_to_fen(total_amount), "currency": "CNY"},
        time_expire=_time_expire_rfc3339(),
        notify_url=settings.WECHAT_NOTIFY_URL,
        pay_type=WeChatPayType.NATIVE,
    )
    if code not in range(200, 300):
        detail = message if isinstance(message, str) else json.dumps(message, ensure_ascii=False)
        raise RuntimeError(f"微信下单失败({code}): {detail}")

    payload = message
    if isinstance(message, str):
        try:
            payload = json.loads(message)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"微信下单响应无法解析: {message}") from e

    code_url = (payload or {}).get("code_url") or ""
    if not code_url:
        raise RuntimeError(f"微信下单未返回 code_url: {payload}")
    return {"code_url": code_url, "mock": False}


def verify_wechat_notify(headers: dict, body: bytes | str) -> dict | None:
    """
    验签并解密回调，成功返回业务数据 dict，失败返回 None。
    """
    if is_wechat_mock_mode():
        if isinstance(body, bytes):
            body = body.decode("utf-8")
        try:
            data = json.loads(body or "{}")
        except json.JSONDecodeError:
            return None
        if data.get("mock_sign") != "mock_ok":
            return None
        return data

    client = get_wechat_client()
    if not client:
        return None
    try:
        result = client.callback(headers, body)
    except Exception:
        logger.exception("WeChat notify verify/decrypt failed")
        return None
    return result if isinstance(result, dict) else None
