# apps/accounts/views.py
import json
import random
import string
import re
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.core.mail import send_mail
from django.conf import settings
from django.core.cache import cache
from captcha.models import CaptchaStore
from captcha.helpers import captcha_image_url
from allauth.account.views import SignupView
from .forms import CustomSignupForm


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

        return JsonResponse({'status': 'success', 'msg': '验证码发送成功'})


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