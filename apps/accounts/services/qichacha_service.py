"""
企查查企业二要素核验（ApiCode 855）。

接口：GET https://api.qichacha.com/ECITwoElVerify/GetInfo
鉴权：Header Token = MD5(AppKey + Timespan + SecretKey).upper()
"""
from __future__ import annotations

import hashlib
import json
import logging
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Optional

from django.conf import settings

logger = logging.getLogger(__name__)

VERIFY_URL = "https://api.qichacha.com/ECITwoElVerify/GetInfo"

# verifyType: 1=核验企业名称, 2=核验法定代表人
VERIFY_TYPE_COMPANY_NAME = 1

VERIFY_RESULT_MESSAGES = {
    0: "统一社会信用代码有误或不存在",
    1: "核验通过",
    2: "单位名称与统一社会信用代码不一致",
}


@dataclass
class TwoElementVerifyResult:
    success: bool
    verify_result: Optional[int]
    message: str
    raw: Optional[dict] = None


def is_qichacha_mock_mode() -> bool:
    if getattr(settings, "QICHACHA_MOCK", False):
        return True
    app_key = getattr(settings, "QICHACHA_APP_KEY", "") or ""
    secret_key = getattr(settings, "QICHACHA_SECRET_KEY", "") or ""
    return not app_key or not secret_key


def _build_headers(app_key: str, secret_key: str) -> dict:
    timespan = str(int(time.time()))
    token = hashlib.md5(f"{app_key}{timespan}{secret_key}".encode("utf-8")).hexdigest().upper()
    return {
        "Token": token,
        "Timespan": timespan,
    }


def verify_company_two_elements(credit_code: str, company_name: str) -> TwoElementVerifyResult:
    """
    核验统一社会信用代码与单位名称是否一致。

    Returns:
        TwoElementVerifyResult: success 仅在 VerifyResult == 1 时为 True
    """
    credit_code = (credit_code or "").strip().upper()
    company_name = (company_name or "").strip()

    if not credit_code or not company_name:
        return TwoElementVerifyResult(
            success=False,
            verify_result=None,
            message="请填写单位名称和统一社会信用代码",
        )

    if is_qichacha_mock_mode():
        # 本地联调：信用代码以 MOCK 开头视为通过
        if credit_code.startswith("MOCK") and len(company_name) >= 2:
            return TwoElementVerifyResult(
                success=True,
                verify_result=1,
                message="核验通过（Mock）",
                raw={"Status": "200", "Result": {"VerifyResult": 1}, "mock": True},
            )
        return TwoElementVerifyResult(
            success=False,
            verify_result=2,
            message="Mock 模式下请使用以 MOCK 开头的信用代码进行测试",
            raw={"mock": True},
        )

    app_key = settings.QICHACHA_APP_KEY
    secret_key = settings.QICHACHA_SECRET_KEY
    params = urllib.parse.urlencode(
        {
            "key": app_key,
            "creditCode": credit_code,
            "verifyName": company_name,
            "verifyType": str(VERIFY_TYPE_COMPANY_NAME),
        }
    )
    url = f"{VERIFY_URL}?{params}"
    request = urllib.request.Request(url, headers=_build_headers(app_key, secret_key), method="GET")

    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            body = response.read().decode("utf-8")
            data = json.loads(body)
    except urllib.error.HTTPError as e:
        logger.exception("企查查二要素核验 HTTP 错误: %s", e)
        return TwoElementVerifyResult(
            success=False,
            verify_result=None,
            message="机构核验服务暂时不可用，请稍后重试",
        )
    except Exception as e:
        logger.exception("企查查二要素核验失败: %s", e)
        return TwoElementVerifyResult(
            success=False,
            verify_result=None,
            message="机构核验服务暂时不可用，请稍后重试",
        )

    status = str(data.get("Status", ""))
    if status and status != "200":
        msg = data.get("Message") or data.get("message") or "机构核验失败"
        logger.warning("企查查返回非成功状态: %s %s", status, msg)
        return TwoElementVerifyResult(
            success=False,
            verify_result=None,
            message=str(msg),
            raw=data,
        )

    result_obj = data.get("Result") or data.get("result") or {}
    if isinstance(result_obj, dict):
        verify_result = result_obj.get("VerifyResult")
        if verify_result is None:
            verify_result = result_obj.get("verifyResult")
    else:
        verify_result = data.get("VerifyResult")

    try:
        verify_result = int(verify_result) if verify_result is not None else None
    except (TypeError, ValueError):
        verify_result = None

    if verify_result == 1:
        return TwoElementVerifyResult(
            success=True,
            verify_result=1,
            message=VERIFY_RESULT_MESSAGES[1],
            raw=data,
        )

    message = VERIFY_RESULT_MESSAGES.get(verify_result, "机构核验未通过")
    return TwoElementVerifyResult(
        success=False,
        verify_result=verify_result,
        message=message,
        raw=data,
    )
