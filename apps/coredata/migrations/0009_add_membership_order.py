import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("coredata", "0008_add_coverage_stats"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="MembershipOrder",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("order_no", models.CharField(db_index=True, max_length=32, unique=True, verbose_name="订单号")),
                ("user_type", models.CharField(max_length=20, verbose_name="用户类型")),
                ("duration", models.CharField(max_length=20, verbose_name="购买时长")),
                ("total_amount", models.DecimalField(decimal_places=2, max_digits=12, verbose_name="订单金额")),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "待支付"),
                            ("paid", "已支付"),
                            ("cancelled", "已取消"),
                            ("expired", "已过期"),
                        ],
                        db_index=True,
                        default="pending",
                        max_length=20,
                        verbose_name="订单状态",
                    ),
                ),
                ("paid_at", models.DateTimeField(blank=True, null=True, verbose_name="支付时间")),
                ("payment_channel", models.CharField(blank=True, default="", max_length=32, verbose_name="支付渠道")),
                ("remark", models.TextField(blank=True, default="", verbose_name="备注")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="创建时间")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="更新时间")),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="membership_orders",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="用户",
                    ),
                ),
            ],
            options={
                "verbose_name": "会员订单",
                "verbose_name_plural": "会员订单",
                "db_table": "membership_order",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="MembershipOrderItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("level", models.CharField(max_length=32, verbose_name="权限级别")),
                ("level_code", models.CharField(max_length=32, verbose_name="级别代码")),
                ("scope_name", models.CharField(max_length=128, verbose_name="权限范围名称")),
                ("scope_id", models.CharField(blank=True, default="", max_length=64, verbose_name="权限范围ID")),
                ("year_price", models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name="年卡单价")),
                ("final_price", models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name="实付金额")),
                (
                    "order",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="items",
                        to="coredata.membershiporder",
                        verbose_name="订单",
                    ),
                ),
            ],
            options={
                "verbose_name": "会员订单明细",
                "verbose_name_plural": "会员订单明细",
                "db_table": "membership_order_item",
            },
        ),
    ]
