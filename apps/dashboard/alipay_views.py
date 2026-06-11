import logging

from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from apps.coredata.services.alipay_service import verify_alipay_notify
from apps.coredata.services.order_service import fulfill_paid_order
from apps.dashboard.views import login_required_json

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["POST"])
def alipay_notify_api(request):
    """支付宝异步通知（验签后开通权限）。"""
    data = request.POST.dict()
    trade_status = data.get("trade_status")
    order_no = data.get("out_trade_no", "")
    trade_no = data.get("trade_no", "")

    logger.info("Alipay notify order=%s status=%s", order_no, trade_status)

    if trade_status not in ("TRADE_SUCCESS", "TRADE_FINISHED"):
        return HttpResponse("success")

    if not verify_alipay_notify(dict(data)):
        logger.warning("Alipay notify verify failed order=%s", order_no)
        return HttpResponse("failure")

    try:
        total = data.get("total_amount")
        fulfill_paid_order(order_no, payment_channel="alipay", alipay_trade_no=trade_no)
        logger.info("Order fulfilled via notify order=%s amount=%s", order_no, total)
    except ValueError as e:
        logger.warning("Fulfill skipped order=%s: %s", order_no, e)
    except Exception as e:
        logger.exception("Fulfill failed order=%s: %s", order_no, e)
        return HttpResponse("failure")

    return HttpResponse("success")


@login_required_json
@require_http_methods(["GET"])
def order_status_api(request):
    """前端轮询订单支付状态。"""
    from django.http import JsonResponse
    from apps.coredata.services.order_service import get_order_status_for_user

    order_no = request.GET.get("order_no", "").strip()
    if not order_no:
        return JsonResponse({"success": False, "message": "缺少订单号"}, status=400)
    try:
        data = get_order_status_for_user(order_no, request.user)
        return JsonResponse({"success": True, "data": data})
    except ValueError as e:
        return JsonResponse({"success": False, "message": str(e)}, status=404)


@csrf_exempt
@require_http_methods(["POST"])
def alipay_mock_notify_api(request):
    """
    Mock 模式模拟支付成功（仅 ALIPAY_MOCK=true 时可用，便于沙箱前联调）。
    POST JSON: {"order_no": "ORD..."}
    """
    import json
    from django.http import JsonResponse
    from apps.coredata.services.alipay_service import is_alipay_mock_mode

    if not is_alipay_mock_mode():
        return JsonResponse({"success": False, "message": "仅 Mock 模式可用"}, status=403)

    try:
        data = json.loads(request.body or "{}")
        order_no = data.get("order_no", "").strip()
        if not order_no:
            return JsonResponse({"success": False, "message": "缺少 order_no"}, status=400)
        result = fulfill_paid_order(order_no, payment_channel="mock")
        return JsonResponse({"success": True, "message": "Mock 支付成功", "data": result})
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "JSON 格式错误"}, status=400)
    except ValueError as e:
        return JsonResponse({"success": False, "message": str(e)}, status=400)
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)
