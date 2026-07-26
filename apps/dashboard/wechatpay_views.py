"""微信支付回调与 Mock 通知。"""
import json
import logging

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from apps.coredata.services.order_service import fulfill_paid_order
from apps.coredata.services.wechatpay_service import is_wechat_mock_mode, verify_wechat_notify

logger = logging.getLogger(__name__)


def _wechat_success_response():
    return JsonResponse({"code": "SUCCESS", "message": "成功"})


def _wechat_fail_response(message: str = "失败", status: int = 400):
    return JsonResponse({"code": "FAIL", "message": message}, status=status)


@csrf_exempt
@require_http_methods(["POST"])
def wechat_notify_api(request):
    """微信支付异步通知（验签解密后开通权限）。"""
    normalized = {
        "Wechatpay-Timestamp": request.headers.get("Wechatpay-Timestamp", ""),
        "Wechatpay-Nonce": request.headers.get("Wechatpay-Nonce", ""),
        "Wechatpay-Signature": request.headers.get("Wechatpay-Signature", ""),
        "Wechatpay-Serial": request.headers.get("Wechatpay-Serial", ""),
        "Wechatpay-Signature-Type": request.headers.get("Wechatpay-Signature-Type", "WECHATPAY2-SHA256-RSA2048"),
    }
    body = request.body

    result = verify_wechat_notify(normalized, body)
    if not result:
        logger.warning("WeChat notify verify failed")
        return _wechat_fail_response("验签失败", status=401)

    # callback 可能包一层 resource，也可能已是业务字段
    resource = result.get("resource") if isinstance(result.get("resource"), dict) else result
    trade_state = resource.get("trade_state") or result.get("trade_state") or ""
    order_no = resource.get("out_trade_no") or result.get("out_trade_no") or ""
    transaction_id = resource.get("transaction_id") or result.get("transaction_id") or ""

    logger.info("WeChat notify order=%s state=%s txn=%s", order_no, trade_state, transaction_id)

    if trade_state and trade_state != "SUCCESS":
        return _wechat_success_response()

    if not order_no:
        return _wechat_fail_response("缺少订单号")

    try:
        fulfill_paid_order(
            order_no,
            payment_channel="wechat",
            trade_no=transaction_id,
        )
    except ValueError as e:
        logger.warning("WeChat fulfill skipped order=%s: %s", order_no, e)
    except Exception as e:
        logger.exception("WeChat fulfill failed order=%s: %s", order_no, e)
        return _wechat_fail_response("处理失败", status=500)

    return _wechat_success_response()


@csrf_exempt
@require_http_methods(["POST"])
def wechat_mock_notify_api(request):
    """Mock 模式模拟微信支付成功（仅 WECHAT_MOCK=true）。"""
    if not is_wechat_mock_mode():
        return JsonResponse({"success": False, "message": "仅 Mock 模式可用"}, status=403)

    try:
        data = json.loads(request.body or "{}")
        order_no = (data.get("order_no") or "").strip()
        if not order_no:
            return JsonResponse({"success": False, "message": "缺少 order_no"}, status=400)
        result = fulfill_paid_order(order_no, payment_channel="mock_wechat", trade_no=f"MOCKWX_{order_no}")
        return JsonResponse({"success": True, "message": "Mock 微信支付成功", "data": result})
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "JSON 格式错误"}, status=400)
    except ValueError as e:
        return JsonResponse({"success": False, "message": str(e)}, status=400)
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)
