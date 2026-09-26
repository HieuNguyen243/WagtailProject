# crm/models.py

from django.db import models
from wagtail.admin.panels import FieldPanel
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet, SnippetViewSetGroup


# ──────────────────────────────────────────────
# Model: Customer
# ──────────────────────────────────────────────
class Customer(models.Model):
    name = models.CharField("Tên khách hàng", max_length=255)
    email = models.EmailField("Email", unique=True)
    phone = models.CharField("Số điện thoại", max_length=20, blank=True)
    created_at = models.DateTimeField("Ngày tạo", auto_now_add=True)

    panels = [
        FieldPanel("name"),
        FieldPanel("email"),
        FieldPanel("phone"),
    ]

    class Meta:
        verbose_name = "Khách hàng"
        verbose_name_plural = "Khách hàng"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


# ──────────────────────────────────────────────
# Model: Order
# ──────────────────────────────────────────────
class Order(models.Model):

    PAYMENT_METHOD_CHOICES = [
        ("MB_eBanking", "MB eBanking"),
        ("ShopeePay", "ShopeePay"),
        ("ZaloPay", "ZaloPay"),
        ("MoMo", "MoMo"),
    ]

    SHIPPING_PROVIDER_CHOICES = [
        ("SPX_Express", "SPX Express"),
        ("J_and_T_Express", "J&T Express"),
        ("GHTK", "GHTK"),
    ]

    STATUS_CHOICES = [
        ("pending", "Đang xử lý"),
        ("completed", "Hoàn thành"),
    ]

    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="orders",
        verbose_name="Khách hàng",
    )
    order_code = models.CharField("Mã đơn hàng", max_length=50, unique=True)
    total_amount = models.DecimalField(
        "Tổng tiền", max_digits=12, decimal_places=2, default=0
    )
    payment_method = models.CharField(
        "Phương thức thanh toán",
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default="MB_eBanking",
    )
    shipping_provider = models.CharField(
        "Đơn vị vận chuyển",
        max_length=20,
        choices=SHIPPING_PROVIDER_CHOICES,
        default="SPX_Express",
    )
    status = models.CharField(
        "Trạng thái",
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
    )

    panels = [
        FieldPanel("customer"),
        FieldPanel("order_code"),
        FieldPanel("total_amount"),
        FieldPanel("payment_method"),
        FieldPanel("shipping_provider"),
        FieldPanel("status"),
    ]

    class Meta:
        verbose_name = "Đơn hàng"
        verbose_name_plural = "Đơn hàng"
        ordering = ["-pk"]

    def __str__(self):
        return f"{self.order_code} – {self.customer.name}"


# ──────────────────────────────────────────────
# Wagtail Snippet ViewSets & Registration
# ──────────────────────────────────────────────
class CustomerViewSet(SnippetViewSet):
    model = Customer
    icon = "user"
    menu_label = "Khách hàng"
    menu_name = "customers"
    list_display = ["name", "email", "phone", "created_at"]
    search_fields = ["name", "email", "phone"]


class OrderViewSet(SnippetViewSet):
    model = Order
    icon = "form"
    menu_label = "Đơn hàng"
    menu_name = "orders"
    list_display = ["order_code", "customer", "total_amount", "payment_method", "shipping_provider", "status"]
    search_fields = ["order_code", "customer__name"]


class CRMViewSetGroup(SnippetViewSetGroup):
    items = (CustomerViewSet, OrderViewSet)
    menu_icon = "folder-open-inverse"
    menu_label = "Quản lý CRM"
    menu_name = "crm"
    menu_order = 200


register_snippet(CRMViewSetGroup)
