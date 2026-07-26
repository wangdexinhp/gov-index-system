from django.conf import settings
from django.db import models


class MembershipOrder(models.Model):
    """会员权限购买订单。"""

    class Status(models.TextChoices):
        PENDING = "pending", "待支付"
        PAID = "paid", "已支付"
        CANCELLED = "cancelled", "已取消"
        EXPIRED = "expired", "已过期"

    order_no = models.CharField("订单号", max_length=32, unique=True, db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="membership_orders",
        verbose_name="用户",
    )
    user_type = models.CharField("用户类型", max_length=20)  # personal / organization
    duration = models.CharField("购买时长", max_length=20)  # year / month / week / day
    total_amount = models.DecimalField("订单金额", max_digits=12, decimal_places=2)
    status = models.CharField(
        "订单状态",
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    paid_at = models.DateTimeField("支付时间", null=True, blank=True)
    expire_at = models.DateTimeField("支付截止时间", null=True, blank=True, db_index=True)
    alipay_trade_no = models.CharField("支付宝交易号", max_length=64, blank=True, default="")
    wechat_transaction_id = models.CharField("微信交易号", max_length=64, blank=True, default="")
    payment_channel = models.CharField("支付渠道", max_length=32, blank=True, default="")
    remark = models.TextField("备注", blank=True, default="")
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        db_table = "membership_order"
        verbose_name = "会员订单"
        verbose_name_plural = "会员订单"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.order_no} ¥{self.total_amount} ({self.get_status_display()})"


class MembershipOrderItem(models.Model):
    """订单权限明细。"""

    order = models.ForeignKey(
        MembershipOrder,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="订单",
    )
    level = models.CharField("权限级别", max_length=32)
    level_code = models.CharField("级别代码", max_length=32)
    scope_name = models.CharField("权限范围名称", max_length=128)
    scope_id = models.CharField("权限范围ID", max_length=64, blank=True, default="")
    year_price = models.DecimalField("年卡单价", max_digits=12, decimal_places=2, default=0)
    final_price = models.DecimalField("实付金额", max_digits=12, decimal_places=2, default=0)

    class Meta:
        db_table = "membership_order_item"
        verbose_name = "会员订单明细"
        verbose_name_plural = "会员订单明细"

    def __str__(self):
        return f"{self.level}·{self.scope_name}"
