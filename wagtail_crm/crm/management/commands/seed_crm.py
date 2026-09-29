import random
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from crm.models import Customer, Order

User = get_user_model()


class Command(BaseCommand):
    help = "Tạo dữ liệu mẫu cho module CRM"

    CUSTOMERS = [
        {"name": "Nguyễn Văn An", "email": "an.nguyen@gmail.com", "phone": "0901234567", "company": "An Phát Tech"},
        {"name": "Trần Thị Bích", "email": "bich.tran@outlook.com", "phone": "0912345678", "company": "Bích Home"},
        {"name": "Lê Hoàng Cường", "email": "cuong.le@yahoo.com", "phone": "0923456789", "company": "Cường Media"},
        {"name": "Phạm Minh Đức", "email": "duc.pham@gmail.com", "phone": "0934567890", "company": "Đức Logistics"},
        {"name": "Hoàng Thị Em", "email": "em.hoang@hotmail.com", "phone": "0945678901", "company": "Em Fashion"},
        {"name": "Vũ Đình Phong", "email": "phong.vu@gmail.com", "phone": "0956789012", "company": "Phong Solutions"},
        {"name": "Đặng Thùy Giang", "email": "giang.dang@outlook.com", "phone": "0967890123", "company": "Giang Studio"},
        {"name": "Bùi Quốc Hải", "email": "hai.bui@gmail.com", "phone": "0978901234", "company": "Hải Retail"},
        {"name": "Ngô Thanh Inh", "email": "inh.ngo@yahoo.com", "phone": "0389012345", "company": "Inh Foods"},
        {"name": "Đỗ Thị Kim", "email": "kim.do@gmail.com", "phone": "0370123456", "company": "Kim Beauty"},
        {"name": "Lý Văn Long", "email": "long.ly@outlook.com", "phone": "0361234567", "company": "Long Trading"},
        {"name": "Trịnh Hồng Mai", "email": "mai.trinh@gmail.com", "phone": "0352345678", "company": "Mai Education"},
        {"name": "Cao Bảo Ngọc", "email": "ngoc.cao@hotmail.com", "phone": "0343456789", "company": "Ngọc Dental"},
        {"name": "Phan Văn Oanh", "email": "oanh.phan@gmail.com", "phone": "0334567890", "company": "Oanh Travel"},
        {"name": "Dương Minh Phúc", "email": "phuc.duong@yahoo.com", "phone": "0325678901", "company": "Phúc Auto"},
        {"name": "Hồ Thị Quỳnh", "email": "quynh.ho@gmail.com", "phone": "0786789012", "company": "Quỳnh Care"},
        {"name": "Tô Đức Rạng", "email": "rang.to@outlook.com", "phone": "0777890123", "company": "Rạng Build"},
        {"name": "Mai Thanh Sơn", "email": "son.mai@gmail.com", "phone": "0768901234", "company": "Sơn Finance"},
        {"name": "Lưu Thị Tâm", "email": "tam.luu@hotmail.com", "phone": "0759012345", "company": "Tâm Interior"},
        {"name": "Châu Văn Uy", "email": "uy.chau@gmail.com", "phone": "0580123456", "company": "Uy Digital"},
    ]

    def handle(self, *args, **options):
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser("admin", "admin@example.com", "admin")
            self.stdout.write(self.style.SUCCESS("Tạo admin: admin / admin"))

        customers = []
        for data in self.CUSTOMERS:
            customer, _ = Customer.objects.get_or_create(
                email=data["email"],
                defaults={**data, "segment": random.choice(["new", "regular", "vip", "risk"])},
            )
            changed = False
            if not customer.company:
                customer.company = data["company"]
                changed = True
            if changed:
                customer.save(update_fields=["company", "updated_at"])
            customers.append(customer)

        for i in range(1, 51):
            code = f"ORD-2026-{i:04d}"
            if Order.objects.filter(order_code=code).exists():
                continue
            Order.objects.create(
                customer=random.choice(customers),
                order_code=code,
                total_amount=Decimal(random.randint(50, 5000)) * Decimal("1000"),
                payment_method=random.choice(["MB_eBanking", "ShopeePay", "ZaloPay", "MoMo"]),
                shipping_provider=random.choice(["SPX_Express", "J_and_T_Express", "GHTK"]),
                status=random.choice(["pending", "completed"]),
            )

        self.stdout.write(self.style.SUCCESS("Seed CRM hoàn tất."))
