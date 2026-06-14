from django.core.management.base import BaseCommand

from apps.coredata.services.order_service import expire_pending_orders


class Command(BaseCommand):
    help = "将超时未支付的订单标记为已过期"

    def handle(self, *args, **options):
        count = expire_pending_orders()
        self.stdout.write(self.style.SUCCESS(f"已过期 {count} 笔待支付订单"))
