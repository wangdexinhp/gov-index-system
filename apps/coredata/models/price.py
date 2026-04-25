# dashboard/models.py
from django.db import models


class PricingConfig(models.Model):
    """价格配置表"""
    
    # 级别代码选择
    LEVEL_CODE_CHOICES = [
        ('national', '全国'),
        ('region', '地区'),
        ('province', '省'),
        ('municipality', '直辖市'),
        ('city', '市'),
    ]
    
    # 用户类型选择
    USER_TYPE_CHOICES = [
        ('personal', '个人用户'),
        ('org', '机构用户'),
    ]
    
    # 时长选择
    DURATION_CHOICES = [
        ('year', '年'),
        ('month', '月'),
        ('week', '周'),
        ('15days', '15天'),
        ('24hour', '24小时'),
    ]
    
    level = models.CharField(max_length=50, verbose_name='权限级别', help_text='全国/地区/省/直辖市/市')
    level_code = models.CharField(max_length=50, choices=LEVEL_CODE_CHOICES, verbose_name='级别代码', db_index=True)
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, verbose_name='用户类型', db_index=True)
    user_type_name = models.CharField(max_length=50, verbose_name='用户类型显示名')
    duration = models.CharField(max_length=20, choices=DURATION_CHOICES, verbose_name='时长', db_index=True)
    duration_name = models.CharField(max_length=20, verbose_name='时长显示名')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='价格（元）')
    days = models.IntegerField(verbose_name='对应天数')
    sort_order = models.IntegerField(default=0, verbose_name='排序序号')
    is_active = models.BooleanField(default=True, verbose_name='是否启用', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'pricing_config'
        verbose_name = '价格配置'
        verbose_name_plural = '价格配置'
        indexes = [
            models.Index(fields=['level_code', 'user_type', 'duration'], name='idx_level_user_duration'),
        ]
        ordering = ['sort_order', 'id']
    
    def __str__(self):
        return f"{self.level}-{self.user_type_name}-{self.duration_name}: ¥{self.price}"


class IndicatorConfig(models.Model):
    """指标配置表"""
    
    USER_TYPE_CHOICES = [
        ('personal', '个人用户'),
        ('org', '机构用户'),
    ]
    
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, verbose_name='用户类型', db_index=True)
    user_type_name = models.CharField(max_length=50, verbose_name='用户类型显示名')
    indicator_name = models.CharField(max_length=200, verbose_name='指标名称')
    indicator_desc = models.CharField(max_length=500, blank=True, default='', verbose_name='指标描述')
    sort_order = models.IntegerField(default=0, verbose_name='排序序号')
    is_active = models.BooleanField(default=True, verbose_name='是否启用', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'indicator_config'
        verbose_name = '指标配置'
        verbose_name_plural = '指标配置'
        indexes = [
            models.Index(fields=['user_type', 'is_active'], name='idx_user_type_active'),
        ]
        ordering = ['user_type', 'sort_order', 'id']
    
    def __str__(self):
        return f"[{self.user_type_name}] {self.indicator_name}"


class DurationMultiplierConfig(models.Model):
    """时长系数配置表"""
    
    DURATION_CODE_CHOICES = [
        ('year', '年卡'),
        ('month', '月卡'),
        ('week', '周卡'),
    ]
    
    duration_code = models.CharField(max_length=20, choices=DURATION_CODE_CHOICES, unique=True, verbose_name='时长代码', db_index=True)
    duration_name = models.CharField(max_length=20, verbose_name='时长显示名')
    multiplier = models.DecimalField(max_digits=10, decimal_places=4, verbose_name='系数值')
    sort_order = models.IntegerField(default=0, verbose_name='排序序号')
    is_active = models.BooleanField(default=True, verbose_name='是否启用', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'duration_multiplier_config'
        verbose_name = '时长系数配置'
        verbose_name_plural = '时长系数配置'
        ordering = ['sort_order', 'id']
    
    def __str__(self):
        return f"{self.duration_name}: {self.multiplier}"