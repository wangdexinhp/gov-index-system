# apps/accounts/views.py
import json
import random
import string
import re,os
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from functools import wraps
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.core.cache import cache
from captcha.models import CaptchaStore
from captcha.helpers import captcha_image_url
from allauth.account.views import SignupView
from .forms import CustomSignupForm
from .models import UserProfile
from .services.qichacha_service import verify_company_two_elements

from alibabacloud_tea_openapi.models import Config  
from alibabacloud_dysmsapi20170525.client import Client
from alibabacloud_dysmsapi20170525 import models as dysmsapi_models
from alibabacloud_tea_util import models as util_models

# 统一社会信用代码：18 位，末位可为数字或 X
CREDIT_CODE_RE = re.compile(r'^[0-9A-Z]{17}[0-9A-ZX]$')


def login_required_json(view_func):
    """未登录时返回 JSON，避免 API 被重定向到登录页。"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'success': False, 'message': '请先登录后再操作'}, status=401)
        return view_func(request, *args, **kwargs)
    return _wrapped_view



class CustomSignupView(SignupView):
    form_class = CustomSignupForm
    template_name = 'account/signup.html'


@method_decorator(csrf_exempt, name='dispatch')
class SendSmsCodeView(View):
    """发送短信验证码视图"""

    def post(self, request):
        mobile = request.POST.get('mobile')

        if not mobile:
            return JsonResponse({'status': 'error', 'msg': '手机号不能为空'})

        # 1. 验证手机号格式
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return JsonResponse({'status': 'error', 'msg': '手机号格式不正确'})

        # 2. 检查是否已注册（通过UserProfile）
        from .models import UserProfile
        if UserProfile.objects.filter(mobile=mobile).exists():
            return JsonResponse({'status': 'error', 'msg': '该手机号已被注册'})

        # 3. 检查发送频率（防止滥用）
        rate_limit_key = f'sms_rate_limit_{mobile}'
        if cache.get(rate_limit_key):
            return JsonResponse({'status': 'error', 'msg': '请等待60秒后重试'})

        # 4. 生成6位随机数字验证码
        sms_code = ''.join(random.choices(string.digits, k=6))

        # 5. 存入缓存（设置5分钟有效期）
        cache_key = f'sms_code_{mobile}'
        cache.set(cache_key, sms_code, timeout=300)  # 5分钟

        # 6. 设置发送频率限制（60秒内只能发一次）
        cache.set(rate_limit_key, '1', timeout=60)

        # 7. 发送短信（这里需要集成短信服务商API）
        # 以下是模拟代码，实际使用需要替换为真实短信API

        # 模拟成功发送
        print(f"发送短信到 {mobile}: 验证码是 {sms_code}")
        # 实际代码示例（以阿里云短信为例）：
        # try:
        #     client = get_sms_client()  # 获取短信客户端
        #     result = client.send_sms(
        #         phone_numbers=mobile,
        #         sign_name='你的签名',
        #         template_code='SMS_123456789',
        #         template_param={'code': sms_code}
        #     )
        #     if result.get('Code') == 'OK':
        #         return JsonResponse({'status': 'success', 'msg': '验证码发送成功'})
        #     else:
        #         cache.delete(cache_key)
        #         cache.delete(rate_limit_key)
        #         return JsonResponse({'status': 'error', 'msg': '短信发送失败'})
        # except Exception as e:
        #     cache.delete(cache_key)
        #     cache.delete(rate_limit_key)
        #     return JsonResponse({'status': 'error', 'msg': f'系统错误: {str(e)}'})

        sms_code = sms_code
        cache_key = f"sms_{mobile}"
        rate_limit_key = f"sms_limit_{mobile}"

        # AK/SK 从环境变量获取
        AK = os.getenv("ALIBABA_CLOUD_AK")
        SK = os.getenv("ALIBABA_CLOUD_SK")

        try:
            # 配置
            config = Config(access_key_id=AK, access_key_secret=SK)
            config.endpoint = "dysmsapi.aliyuncs.com"
            client = Client(config)
            
            # 创建发送请求对象
            # send_sms_request = dysmsapi_models.SendSmsRequest(
            #     phone_numbers=mobile,           # 注意：下划线命名
            #     sign_name="阿里云",
            #     template_code="SMS_154950909",
            #     template_param=json.dumps({"code": sms_code})
            # )
            send_sms_request = dysmsapi_models.SendSmsRequest(
                phone_numbers=mobile,
                sign_name="海杰人文智能",                     # 测试专用签名，必须是“阿里云”
                template_code="SMS_327784823",         # 测试专用模板CODE
                template_param=json.dumps({
                    "code": sms_code,                  # 模板里的${code}变量
                    "minute": "5"                      # 模板里的${minute}变量
                })
            )
            
            # 发送短信（可选：添加运行时配置）
            runtime = util_models.RuntimeOptions()
            result = client.send_sms_with_options(send_sms_request, runtime)
            
            # 判断结果
            if result.body.code == "OK":
                return JsonResponse({'status': 'success', 'msg': '发送成功'})
            else:
                cache.delete(cache_key)
                cache.delete(rate_limit_key)
                return JsonResponse({'status': 'error', 'msg': result.body.message})
                
        except Exception as e:
            cache.delete(cache_key)
            cache.delete(rate_limit_key)
            return JsonResponse({'status': 'error', 'msg': f'错误：{str(e)}'})

        # return JsonResponse({'status': 'success', 'msg': '验证码发送成功'})


@method_decorator(csrf_exempt, name='dispatch')
class RefreshCaptchaView(View):
    """刷新验证码视图"""

    def get(self, request):
        return self._generate_response()

    def post(self, request):
        return self._generate_response()

    def _generate_response(self):
        try:
            key = CaptchaStore.generate_key()
            image_url = captcha_image_url(key)

            return JsonResponse({
                'status': 'success',
                'key': key,
                'image_url': image_url
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)


# 可选：验证手机号是否已注册的视图
@method_decorator(csrf_exempt, name='dispatch')
class CheckMobileView(View):
    """检查手机号是否已注册"""

    def post(self, request):
        mobile = request.POST.get('mobile')

        if not mobile:
            return JsonResponse({'status': 'error', 'msg': '手机号不能为空'})

        # 验证格式
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return JsonResponse({'status': 'error', 'msg': '手机号格式不正确'})

        # 检查是否已注册
        from .models import UserProfile
        if UserProfile.objects.filter(mobile=mobile).exists():
            return JsonResponse({'status': 'error', 'msg': '该手机号已被注册'})

        return JsonResponse({'status': 'success', 'msg': '手机号可用'})


def _org_status_payload(profile: UserProfile) -> dict:
    return {
        'org_name': profile.org_name or '',
        'org_credit_code': profile.org_credit_code or '',
        'org_verify_status': profile.org_verify_status,
        'org_verify_status_display': profile.get_org_verify_status_display(),
        'is_org_verified': profile.is_org_verified,
        'org_verified_at': profile.org_verified_at.isoformat() if profile.org_verified_at else None,
        'org_verify_message': profile.org_verify_message or '',
    }


@login_required_json
@require_http_methods(['GET'])
def org_verify_status_api(request):
    """查询当前用户机构认证状态。"""
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    return JsonResponse({'success': True, 'data': _org_status_payload(profile)})


@login_required_json
@require_http_methods(['POST'])
def org_verify_api(request):
    """提交机构二要素核验（单位名称 + 统一社会信用代码）。"""
    try:
        data = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': '请求数据格式错误'}, status=400)

    org_name = (data.get('org_name') or '').strip()
    org_credit_code = (data.get('org_credit_code') or '').strip().upper()

    if not org_name:
        return JsonResponse({'success': False, 'message': '请填写单位名称'}, status=400)
    if not org_credit_code:
        return JsonResponse({'success': False, 'message': '请填写统一社会信用代码'}, status=400)
    if not (
        CREDIT_CODE_RE.match(org_credit_code)
        or org_credit_code.startswith('MOCK')  # Mock 联调
    ):
        return JsonResponse({'success': False, 'message': '统一社会信用代码格式不正确'}, status=400)

    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if profile.is_org_verified and profile.org_credit_code == org_credit_code and profile.org_name == org_name:
        return JsonResponse({
            'success': True,
            'message': '机构已认证',
            'data': _org_status_payload(profile),
        })

    result = verify_company_two_elements(org_credit_code, org_name)
    profile.org_name = org_name
    profile.org_credit_code = org_credit_code
    profile.org_verify_message = result.message

    if result.success:
        profile.org_verify_status = UserProfile.ORG_VERIFY_VERIFIED
        profile.org_verified_at = timezone.now()
        profile.save(update_fields=[
            'org_name', 'org_credit_code', 'org_verify_status',
            'org_verified_at', 'org_verify_message', 'updated_at',
        ])
        return JsonResponse({
            'success': True,
            'message': result.message,
            'data': _org_status_payload(profile),
        })

    profile.org_verify_status = UserProfile.ORG_VERIFY_FAILED
    profile.org_verified_at = None
    profile.save(update_fields=[
        'org_name', 'org_credit_code', 'org_verify_status',
        'org_verified_at', 'org_verify_message', 'updated_at',
    ])
    return JsonResponse({
        'success': False,
        'message': result.message,
        'data': _org_status_payload(profile),
    }, status=400)