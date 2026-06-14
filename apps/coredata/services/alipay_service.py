"""
支付宝当面付（扫码）封装。沙箱 / Mock 模式可本地联调。
"""
import logging
from decimal import Decimal
from typing import Optional

from django.conf import settings

logger = logging.getLogger(__name__)


def _format_private_key(key: str) -> str:
    key = (key or "").strip()
    if not key or "BEGIN" in key:
        return key
    return (
        "-----BEGIN RSA PRIVATE KEY-----\n"
        + "\n".join(key[i : i + 64] for i in range(0, len(key), 64))
        + "\n-----END RSA PRIVATE KEY-----"
    )


def _format_public_key(key: str) -> str:
    key = (key or "").strip()
    if not key or "BEGIN" in key:
        return key
    return (
        "-----BEGIN PUBLIC KEY-----\n"
        + "\n".join(key[i : i + 64] for i in range(0, len(key), 64))
        + "\n-----END PUBLIC KEY-----"
    )


def is_alipay_mock_mode() -> bool:
    if getattr(settings, "ALIPAY_MOCK", False):
        return True
    app_id = getattr(settings, "ALIPAY_APP_ID", "")
    private_key = getattr(settings, "ALIPAY_PRIVATE_KEY", "")
    return not app_id or app_id.startswith("mock_") or not private_key


def get_alipay_client():
    if is_alipay_mock_mode():
        return None
    from alipay import AliPay

    return AliPay(
        appid=settings.ALIPAY_APP_ID,
        app_notify_url=settings.ALIPAY_NOTIFY_URL,
        app_private_key_string=_format_private_key(settings.ALIPAY_PRIVATE_KEY),
        alipay_public_key_string=_format_public_key(settings.ALIPAY_PUBLIC_KEY),
        sign_type="RSA2",
        debug=settings.ALIPAY_SANDBOX,
    )


def create_face_to_face_payment(order_no: str, total_amount: Decimal, subject: str) -> dict:
    amount_str = f"{Decimal(total_amount):.2f}"
    if is_alipay_mock_mode():
        qr = f"https://mock.alipay.dev/qrcode?order={order_no}&amount={amount_str}"
        logger.info("Alipay MOCK precreate order=%s amount=%s", order_no, amount_str)
        return {"qr_code": qr, "mock": True}

    client = get_alipay_client()
    if not client:
        raise RuntimeError("支付宝客户端未配置")

    result = client.api_alipay_trade_precreate(
        out_trade_no=order_no,
        total_amount=amount_str,
        subject=subject[:256],
        timeout_express=f"{settings.ORDER_PAY_TIMEOUT_MINUTES}m",
    )
    if result.get("code") != "10000":
        raise RuntimeError(result.get("sub_msg") or result.get("msg") or "支付宝下单失败")
    return {"qr_code": result.get("qr_code"), "mock": False}


def verify_alipay_notify(data: dict) -> bool:
    if is_alipay_mock_mode():
        return data.get("mock_sign") == "mock_ok"
    client = get_alipay_client()
    if not client:
        return False
    payload = dict(data)
    signature = payload.pop("sign", None)
    payload.pop("sign_type", None)
    return client.verify(payload, signature)
