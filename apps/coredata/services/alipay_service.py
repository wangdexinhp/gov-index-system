"""
支付宝当面付（扫码）封装。
支持：
- 公钥模式（AliPay）—— 应用私钥 + 支付宝公钥
- 公钥证书模式（DCAliPay）—— 应用私钥 + 三份证书
沙箱 / Mock 模式可本地联调。
"""
import logging
from decimal import Decimal
from pathlib import Path

from django.conf import settings

logger = logging.getLogger(__name__)


def _pem_wrap(body: str, header: str, footer: str) -> str:
    body = "".join(body.split())
    lines = "\n".join(body[i : i + 64] for i in range(0, len(body), 64))
    return f"-----{header}-----\n{lines}\n-----{footer}-----"


def _try_export_pkcs1(pem: str, password: bytes | None = None) -> str | None:
    """尝试把任意 PEM/DER 私钥导出为 PKCS#1 PEM。"""
    raw = pem.encode("utf-8") if isinstance(pem, str) else pem

    # 1) Cryptodome
    try:
        from Cryptodome.PublicKey import RSA

        rsa_key = RSA.import_key(raw, passphrase=password)
        return rsa_key.export_key(format="PEM", pkcs=1).decode("utf-8")
    except Exception:
        pass

    # 2) cryptography PEM / DER
    try:
        from cryptography.hazmat.primitives.serialization import (
            Encoding,
            NoEncryption,
            PrivateFormat,
            load_pem_private_key,
            load_der_private_key,
        )

        try:
            private_key = load_pem_private_key(raw, password=password)
        except Exception:
            import base64

            text = raw.decode("utf-8", errors="ignore")
            text = "".join(
                line for line in text.splitlines()
                if line and not line.startswith("-----")
            )
            der = base64.b64decode(text)
            private_key = load_der_private_key(der, password=password)

        return private_key.private_bytes(
            Encoding.PEM,
            PrivateFormat.TraditionalOpenSSL,
            NoEncryption(),
        ).decode("utf-8")
    except Exception:
        return None


def _format_private_key(key: str) -> str:
    """
    规范化应用私钥为 PKCS#1 PEM（BEGIN RSA PRIVATE KEY）。
    兼容：PKCS#1 / PKCS#8 / 加密 PKCS#8（需 ALIPAY_PRIVATE_KEY_PASSWORD）。
    """
    key = (key or "").strip().replace("\r\n", "\n").replace("\r", "\n")
    if key.startswith("\ufeff"):
        key = key.lstrip("\ufeff")
    if not key:
        return key

    password_raw = getattr(settings, "ALIPAY_PRIVATE_KEY_PASSWORD", "") or ""
    password = password_raw.encode("utf-8") if password_raw else None

    if "ENCRYPTED PRIVATE KEY" in key and not password:
        raise ValueError(
            "应用私钥已加密（BEGIN ENCRYPTED PRIVATE KEY），请在 .env 设置 "
            "ALIPAY_PRIVATE_KEY_PASSWORD=生成密钥时的密码；"
            "或用 openssl 解密成非加密私钥后再用。"
        )

    candidates = [key]
    if "BEGIN" not in key:
        body = key
        candidates = [
            _pem_wrap(body, "BEGIN PRIVATE KEY", "END PRIVATE KEY"),
            _pem_wrap(body, "BEGIN RSA PRIVATE KEY", "END RSA PRIVATE KEY"),
        ]
    elif "BEGIN PRIVATE KEY" in key and "BEGIN RSA PRIVATE KEY" not in key:
        body = "\n".join(
            line for line in key.splitlines() if line and not line.startswith("-----")
        )
        candidates = [
            key,
            _pem_wrap(body, "BEGIN PRIVATE KEY", "END PRIVATE KEY"),
            _pem_wrap(body, "BEGIN RSA PRIVATE KEY", "END RSA PRIVATE KEY"),
        ]
    elif "BEGIN RSA PRIVATE KEY" in key:
        body = "\n".join(
            line for line in key.splitlines() if line and not line.startswith("-----")
        )
        candidates = [
            key,
            _pem_wrap(body, "BEGIN PRIVATE KEY", "END PRIVATE KEY"),
        ]

    # 未加密私钥若误配了密码，Cryptodome 会直接失败；先试密码，再回退无密码。
    passwords = [password] if password else [None]
    if password:
        passwords.append(None)

    for candidate in candidates:
        for pwd in passwords:
            exported = _try_export_pkcs1(candidate, password=pwd)
            if exported:
                return exported

    preview = key.splitlines()[0] if key else "(empty)"
    raise ValueError(
        f"应用私钥格式无法识别（文件首行: {preview}）。"
        "若是加密私钥请检查 ALIPAY_PRIVATE_KEY_PASSWORD；"
        "未加密私钥请将 ALIPAY_PRIVATE_KEY_PASSWORD 留空，"
        "并用 openssl pkey -in key.pem -traditional -out app_private_key.pem 转为 PKCS#1。"
    )



def _resolve_path(path_value: str) -> Path | None:
    raw = (path_value or "").strip()
    if not raw:
        return None
    path = Path(raw)
    if not path.is_absolute():
        path = Path(settings.BASE_DIR) / path
    return path


def _load_text(path_value: str = "", content_value: str = "", label: str = "") -> str:
    """优先读文件路径，其次读环境变量内联内容。"""
    path = _resolve_path(path_value)
    if path is not None and path.is_file():
        return path.read_text(encoding="utf-8").strip()
    content = (content_value or "").strip()
    if content:
        return content
    if path is not None:
        raise FileNotFoundError(f"支付宝{label}未配置或文件不存在: {path}")
    raise FileNotFoundError(f"支付宝{label}未配置")


def _format_public_key(key: str) -> str:
    """规范化公钥为 PEM（BEGIN PUBLIC KEY）。"""
    key = (key or "").strip().replace("\r\n", "\n").replace("\r", "\n")
    if key.startswith("\ufeff"):
        key = key.lstrip("\ufeff")
    if not key:
        return key
    if "BEGIN PUBLIC KEY" in key:
        return key
    if "BEGIN" in key:
        return key
    return _pem_wrap(key, "BEGIN PUBLIC KEY", "END PUBLIC KEY")


def _load_private_key() -> str:
    return _format_private_key(
        _load_text(
            getattr(settings, "ALIPAY_PRIVATE_KEY_PATH", ""),
            getattr(settings, "ALIPAY_PRIVATE_KEY", ""),
            label="应用私钥",
        )
    )


def _load_alipay_public_key() -> str:
    return _format_public_key(
        _load_text(
            getattr(settings, "ALIPAY_PUBLIC_KEY_PATH", ""),
            getattr(settings, "ALIPAY_PUBLIC_KEY", ""),
            label="支付宝公钥",
        )
    )


def _load_app_cert() -> str:
    return _load_text(
        getattr(settings, "ALIPAY_APP_CERT_PATH", ""),
        getattr(settings, "ALIPAY_APP_CERT", ""),
        label="应用公钥证书",
    )


def _load_alipay_public_cert() -> str:
    return _load_text(
        getattr(settings, "ALIPAY_PUBLIC_CERT_PATH", ""),
        getattr(settings, "ALIPAY_PUBLIC_CERT", ""),
        label="支付宝公钥证书",
    )


def _load_root_cert() -> str:
    return _load_text(
        getattr(settings, "ALIPAY_ROOT_CERT_PATH", ""),
        getattr(settings, "ALIPAY_ROOT_CERT", ""),
        label="支付宝根证书",
    )


def is_alipay_mock_mode() -> bool:
    if getattr(settings, "ALIPAY_MOCK", False):
        return True
    app_id = getattr(settings, "ALIPAY_APP_ID", "")
    return not app_id or app_id.startswith("mock_")


def get_alipay_sign_mode() -> str:
    """
    key  = 公钥模式（AliPay）
    cert = 公钥证书模式（DCAliPay）
    未显式配置时：有支付宝公钥文件则用 key，否则用 cert。
    """
    mode = (getattr(settings, "ALIPAY_SIGN_MODE", "") or "").strip().lower()
    if mode in ("key", "pubkey", "public", "public_key"):
        return "key"
    if mode in ("cert", "certificate", "certs"):
        return "cert"
    pub_path = _resolve_path(getattr(settings, "ALIPAY_PUBLIC_KEY_PATH", "") or "")
    if pub_path is not None and pub_path.is_file():
        return "key"
    if (getattr(settings, "ALIPAY_PUBLIC_KEY", "") or "").strip():
        return "key"
    return "cert"


def get_alipay_client():
    if is_alipay_mock_mode():
        return None

    mode = get_alipay_sign_mode()
    if mode == "key":
        from alipay import AliPay

        return AliPay(
            appid=settings.ALIPAY_APP_ID,
            app_notify_url=settings.ALIPAY_NOTIFY_URL,
            app_private_key_string=_load_private_key(),
            alipay_public_key_string=_load_alipay_public_key(),
            sign_type="RSA2",
            debug=settings.ALIPAY_SANDBOX,
        )

    from alipay import DCAliPay

    return DCAliPay(
        appid=settings.ALIPAY_APP_ID,
        app_notify_url=settings.ALIPAY_NOTIFY_URL,
        app_private_key_string=_load_private_key(),
        app_public_key_cert_string=_load_app_cert(),
        alipay_public_key_cert_string=_load_alipay_public_cert(),
        alipay_root_cert_string=_load_root_cert(),
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
