# apps/accounts/models.py
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    """用户扩展资料"""

    ORG_VERIFY_PENDING = 'pending'
    ORG_VERIFY_VERIFIED = 'verified'
    ORG_VERIFY_FAILED = 'failed'
    ORG_VERIFY_STATUS_CHOICES = [
        (ORG_VERIFY_PENDING, '未认证'),
        (ORG_VERIFY_VERIFIED, '已认证'),
        (ORG_VERIFY_FAILED, '认证失败'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='用户'
    )

    # 自定义字段
    mobile = models.CharField('手机号', max_length=11, blank=True, null=True)
    membership_expires_at = models.DateTimeField('会员过期时间', blank=True, null=True)
    membership_level = models.CharField(
        '当前会员类型',
        max_length=20,
        choices=[
            ('free', '无会员'),
            ('day', '日会员'),
            ('week', '周会员'),
            ('month', '月会员'),
            ('year', '年会员'),
            ('admin', '管理员'),

        ],
        default='free'
    )
    membership_scope_city=models.TextField('查看城市权限',default='[]', blank=True) # 默认存储空JSON数组字符串
    membership_scope_item=models.TextField('查看指标权限',default='[]', blank=True) # 默认存储空JSON数组字符串

    # 机构认证（企查查企业二要素）
    org_name = models.CharField('单位名称', max_length=200, blank=True, default='')
    org_credit_code = models.CharField('统一社会信用代码', max_length=32, blank=True, default='')
    org_verify_status = models.CharField(
        '机构认证状态',
        max_length=20,
        choices=ORG_VERIFY_STATUS_CHOICES,
        default=ORG_VERIFY_PENDING,
    )
    org_verified_at = models.DateTimeField('机构认证通过时间', blank=True, null=True)
    org_verify_message = models.CharField('机构认证说明', max_length=255, blank=True, default='')

    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '用户资料'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.user.username} 的资料"

    @property
    def is_membership_active(self):
        """检查会员是否有效"""
        if not self.membership_expires_at:
            return False
        from django.utils import timezone
        return self.membership_expires_at > timezone.now()

    @property
    def is_org_verified(self):
        """是否已通过机构认证"""
        return self.org_verify_status == self.ORG_VERIFY_VERIFIED


# 信号：创建用户时自动创建资料
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    try:
        instance.profile.save()
    except:
        UserProfile.objects.get_or_create(user=instance)