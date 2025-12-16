# apps/accounts/forms.py
from django import forms
from captcha.fields import CaptchaField
from allauth.account.forms import SignupForm
from django.contrib.auth.models import User
from .models import UserProfile
import re


class CustomSignupForm(SignupForm):
    """自定义注册表单 - 使用手机号注册"""

    # 1. 重写email字段为可选（或不显示）
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 将email设为非必填
        self.fields['email'].required = False
        # 如果你想完全移除email字段，可以注释掉上面这行，然后：
        # self.fields.pop('email')

    # 2. 添加手机号字段（必填）
    mobile = forms.CharField(
        label='手机号',
        max_length=11,
        widget=forms.TextInput(attrs={
            'class': 'border-b-2 border-t-0 border-x-0 border-black p-3 w-full focus:border-dark-gray focus:outline-none',
            'placeholder': '请输入11位手机号',
            'autocomplete': 'tel'
        })
    )

    # 3. 添加短信验证码字段
    sms_code = forms.CharField(
        label='短信验证码',
        max_length=6,
        widget=forms.TextInput(attrs={
            'class': 'border-b-2 border-t-0 border-x-0 border-black p-3 w-full focus:border-dark-gray focus:outline-none',
            'placeholder': '请输入6位短信验证码'
        })
    )

    # 4. 图形验证码字段
    captcha = CaptchaField(
        label='图形验证码',
        error_messages={'invalid': '验证码错误'}
    )

    def clean_mobile(self):
        """验证手机号"""
        mobile = self.cleaned_data.get('mobile')

        # 验证手机号格式
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            raise forms.ValidationError('手机号格式不正确')

        # 验证手机号是否已注册（检查UserProfile）
        if UserProfile.objects.filter(mobile=mobile).exists():
            raise forms.ValidationError('该手机号已被注册')

        # 也可以检查User表中的email字段（如果之前用手机号注册过）
        # 通常我们会把手机号作为username或email的替代
        return mobile

    def clean(self):
        cleaned_data = super().clean()
        mobile = cleaned_data.get('mobile')
        sms_code = cleaned_data.get('sms_code')

        # 验证短信验证码
        if mobile and sms_code:
            from django.core.cache import cache
            cache_key = f'sms_code_{mobile}'
            cached_code = cache.get(cache_key)

            if not cached_code or sms_code != cached_code:
                self.add_error('sms_code', '短信验证码错误或已过期')

        return cleaned_data

    def save(self, request):
        """保存用户信息"""
        # 获取手机号
        mobile = self.cleaned_data.get('mobile')

        # 处理email：如果用户没有输入email，使用手机号作为email
        # 这是为了兼容Django的User模型，它要求email字段唯一
        if not self.cleaned_data.get('email'):
            self.cleaned_data['email'] = f"{mobile}@mobile.user"

        # 调用父类方法创建用户
        user = super().save(request)

        # 保存手机号到UserProfile
        profile, created = UserProfile.objects.get_or_create(user=user)
        profile.mobile = mobile

        # 设置默认会员过期时间
        from django.utils import timezone
        from datetime import timedelta
        if not profile.membership_expires_at:
            profile.membership_expires_at = timezone.now() + timedelta(days=30)

        profile.save()

        # 清理验证码缓存
        from django.core.cache import cache
        cache.delete(f'sms_code_{mobile}')

        return user