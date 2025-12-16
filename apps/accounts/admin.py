# apps/accounts/admin.py
import json
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from django.utils import timezone
from .models import UserProfile


class UserProfileInline(admin.StackedInline):
    """在用户管理页面内联显示用户资料"""
    model = UserProfile
    can_delete = False
    verbose_name_plural = '用户扩展资料'
    fields = (
        'mobile',
        'membership_level',
        'membership_expires_at',
        'formatted_membership_scope_city',
        'formatted_membership_scope_item',
        'created_at',
        'updated_at',
    )
    readonly_fields = (
        'formatted_membership_scope_city',
        'formatted_membership_scope_item',
        'created_at',
        'updated_at',
    )

    def formatted_membership_scope_city(self, obj):
        """格式化显示城市权限"""
        try:
            city_list = json.loads(obj.membership_scope_city)
            if city_list:
                return ', '.join(city_list)
            return '无限制'
        except:
            return '格式错误'

    formatted_membership_scope_city.short_description = '城市权限'

    def formatted_membership_scope_item(self, obj):
        """格式化显示指标权限"""
        try:
            item_list = json.loads(obj.membership_scope_item)
            if item_list:
                return ', '.join(item_list)
            return '无限制'
        except:
            return '格式错误'

    formatted_membership_scope_item.short_description = '指标权限'


class CustomUserAdmin(UserAdmin):
    """自定义用户管理界面"""
    inlines = (UserProfileInline,)
    list_display = (
        'username',
        'email',
        'get_mobile',
        'get_membership_level',
        'get_membership_expires',
        'is_active',
        'is_staff',
        'date_joined'
    )
    list_filter = (
        'is_staff',
        'is_superuser',
        'is_active',
        'profile__membership_level',
        'date_joined',
    )
    search_fields = (
        'username',
        'email',
        'profile__mobile',
    )
    ordering = ('-date_joined',)
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('个人信息', {'fields': ('first_name', 'last_name', 'email')}),
        ('权限', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('重要日期', {'fields': ('last_login', 'date_joined')}),
    )

    # 自定义方法用于列表显示
    def get_mobile(self, obj):
        """显示手机号"""
        if hasattr(obj, 'profile') and obj.profile.mobile:
            return obj.profile.mobile
        return '-'

    get_mobile.short_description = '手机号'

    def get_membership_level(self, obj):
        """显示会员类型"""
        if hasattr(obj, 'profile'):
            level_display = dict(UserProfile._meta.get_field('membership_level').choices).get(
                obj.profile.membership_level, obj.profile.membership_level
            )
            return level_display
        return '-'

    get_membership_level.short_description = '会员类型'

    def get_membership_expires(self, obj):
        """显示会员过期状态"""
        if hasattr(obj, 'profile') and obj.profile.membership_expires_at:
            if obj.profile.is_membership_active:
                return format_html(
                    '<span style="color: green;">{}</span>',
                    obj.profile.membership_expires_at.strftime('%Y-%m-%d %H:%M')
                )
            else:
                return format_html(
                    '<span style="color: red;">{} (已过期)</span>',
                    obj.profile.membership_expires_at.strftime('%Y-%m-%d %H:%M')
                )
        return '-'

    get_membership_expires.short_description = '会员过期时间'

    def get_queryset(self, request):
        """优化查询，避免N+1问题"""
        return super().get_queryset(request).select_related('profile')


# 重新注册User模型，使用自定义管理类
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """用户资料独立管理界面"""
    list_display = (
        'user',
        'mobile',
        'membership_level_display',
        'membership_expires_at_display',
        'is_membership_active_display',
        'created_at',
    )
    list_filter = (
        'membership_level',
        'created_at',
    )
    search_fields = (
        'user__username',
        'user__email',
        'mobile',
    )
    readonly_fields = (
        'created_at',
        'updated_at',
        'formatted_membership_scope_city',
        'formatted_membership_scope_item',
    )
    fieldsets = (
        ('用户关联', {
            'fields': ('user',)
        }),
        ('基本信息', {
            'fields': ('mobile',)
        }),
        ('会员信息', {
            'fields': ('membership_level', 'membership_expires_at')
        }),
        ('权限信息', {
            'fields': ('formatted_membership_scope_city', 'formatted_membership_scope_item'),
            'description': 'JSON格式存储的权限数据，请在用户页面编辑'
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    ordering = ('-created_at',)

    # 自定义显示方法
    def membership_level_display(self, obj):
        """显示会员类型的中文名称"""
        level_dict = dict(UserProfile._meta.get_field('membership_level').choices)
        return level_dict.get(obj.membership_level, obj.membership_level)

    membership_level_display.short_description = '会员类型'

    def membership_expires_at_display(self, obj):
        """格式化显示过期时间"""
        if obj.membership_expires_at:
            return obj.membership_expires_at.strftime('%Y-%m-%d %H:%M')
        return '无'

    membership_expires_at_display.short_description = '过期时间'

    def is_membership_active_display(self, obj):
        """显示会员状态"""
        if obj.is_membership_active:
            return format_html('<span style="color: green; font-weight: bold;">有效</span>')
        else:
            return format_html('<span style="color: red;">无效</span>')

    is_membership_active_display.short_description = '会员状态'

    def formatted_membership_scope_city(self, obj):
        """格式化显示城市权限"""
        try:
            city_list = json.loads(obj.membership_scope_city)
            if city_list:
                return format_html('<br>'.join(city_list))
            return '无权限'
        except:
            return '格式错误'

    formatted_membership_scope_city.short_description = '城市权限'

    def formatted_membership_scope_item(self, obj):
        """格式化显示指标权限"""
        try:
            item_list = json.loads(obj.membership_scope_item)
            if item_list:
                return format_html('<br>'.join(item_list))
            return '无权限'
        except:
            return '格式错误'

    formatted_membership_scope_item.short_description = '指标权限'