# crm/management/commands/seed_crm.py

import random
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from crm.models import Customer, Order

User = get_user_model()


class Command(BaseCommand):
    help = "Tạo dữ liệu mẫu cho module CRM (20 khách hàng, 50 đơn hàng)"

    # ── Dữ liệu gốc ──────────────────────────────────────────
    CUSTOMERS = [
        {"name": "Nguyễn Văn An",      "email": "an.nguyen@gmail.com",        "phone": "0901234567"},
        {"name": "Trần Thị Bích",      "email": "bich.tran@outlook.com",      "phone": "0912345678"},
        {"name": "Lê Hoàng Cường",     "email": "cuong.le@yahoo.com",         "phone": "0923456789"},
        {"name": "Phạm Minh Đức",      "email": "duc.pham@gmail.com",         "phone": "0934567890"},
        {"name": "Hoàng Thị Em",       "email": "em.hoang@hotmail.com",       "phone": "0945678901"},
        {"name": "Vũ Đình Phong",      "email": "phong.vu@gmail.com",         "phone": "0956789012"},
        {"name": "Đặng Thùy Giang",    "email": "giang.dang@outlook.com",     "phone": "0967890123"},
        {"name": "Bùi Quốc Hải",       "email": "hai.bui@gmail.com",          "phone": "0978901234"},
        {"name": "Ngô Thanh Inh",      "email": "inh.ngo@yahoo.com",          "phone": "0389012345"},
        {"name": "Đỗ Thị Kim",         "email": "kim.do@gmail.com",           "phone": "0370123456"},
        {"name": "Lý Văn Long",        "email": "long.ly@outlook.com",        "phone": "0361234567"},
        {"name": "Trịnh Hồng Mai",     "email": "mai.trinh@gmail.com",        "phone": "0352345678"},
        {"name": "Cao Bảo Ngọc",       "email": "ngoc.cao@hotmail.com",       "phone": "0343456789"},
        {"name": "Phan Văn Oanh",      "email": "oanh.phan@gmail.com",        "phone": "0334567890"},
        {"name": "Dương Minh Phúc",    "email": "phuc.duong@yahoo.com",       "phone": "0325678901"},
        {"name": "Hồ Thị Quỳnh",      "email": "quynh.ho@gmail.com",         "phone": "0786789012"},
        {"name": "Tô Đức Rạng",       "email": "rang.to@outlook.com",        "phone": "0777890123"},
        {"name": "Mai Thanh Sơn",      "email": "son.mai@gmail.com",          "phone": "0768901234"},
        {"name": "Lưu Thị Tâm",       "email": "tam.luu@hotmail.com",        "phone": "0759012345"},
        {"name": "Châu Văn Uy",        "email": "uy.chau@gmail.com",          "phone": "0580123456"},
    ]

    PAYMENT_METHODS = ["MB_eBanking", "ShopeePay", "ZaloPay", "MoMo"]
    SHIPPING_PROVIDERS = ["SPX_Express", "J_and_T_Express", "GHTK"]
    STATUSES = ["pending", "completed"]

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING(">> Bat dau tao du lieu mau CRM..."))

        # ── Tạo tài khoản admin mặc định ──────────────────────
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser(
                username="admin",
                email="admin@example.com",
                password="admin",
            )
            self.stdout.write("   [OK] Superuser: admin / admin (da tao)")
        else:
            self.stdout.write("   [--] Superuser: admin da ton tai, bo qua")

        # ── Tạo khách hàng ────────────────────────────────────
        customers = []
        created_count = 0
        for data in self.CUSTOMERS:
            customer, created = Customer.objects.get_or_create(
                email=data["email"],
                defaults={"name": data["name"], "phone": data["phone"]},
            )
            customers.append(customer)
            if created:
                created_count += 1

        self.stdout.write(f"   [OK] Khach hang: {created_count} moi tao, {len(customers) - created_count} da ton tai")

        # ── Tạo đơn hàng ──────────────────────────────────────
        order_count = 0
        for i in range(1, 51):
            order_code = f"ORD-2026-{i:04d}"
            if Order.objects.filter(order_code=order_code).exists():
                continue

            Order.objects.create(
                customer=random.choice(customers),
                order_code=order_code,
                total_amount=Decimal(random.randint(50, 5000)) * Decimal("1000"),
                payment_method=random.choice(self.PAYMENT_METHODS),
                shipping_provider=random.choice(self.SHIPPING_PROVIDERS),
                status=random.choice(self.STATUSES),
            )
            order_count += 1

        self.stdout.write(f"   [OK] Don hang : {order_count} moi tao")
        self.stdout.write(self.style.SUCCESS("\n>> Hoan tat! Truy cap /admin/ de kiem tra du lieu."))
