from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("coredata", "0009_add_membership_order"),
    ]

    operations = [
        migrations.AddField(
            model_name="membershiporder",
            name="alipay_trade_no",
            field=models.CharField(blank=True, default="", max_length=64, verbose_name="支付宝交易号"),
        ),
        migrations.AddField(
            model_name="membershiporder",
            name="expire_at",
            field=models.DateTimeField(blank=True, db_index=True, null=True, verbose_name="支付截止时间"),
        ),
    ]
