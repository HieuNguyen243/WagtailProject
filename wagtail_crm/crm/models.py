from decimal import Decimal

from django.db import models
from django.utils.html import format_html
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, ObjectList, TabbedInterface


class Customer(models.Model):
    SEGMENT_CHOICES = [
        ("new", "Khách mới"),
        ("regular", "Khách thường xuyên"),
        ("vip", "Khách VIP"),
        ("risk", "Có nguy cơ rời bỏ"),
    ]

    name = models.CharField("Tên khách hàng", max_length=255)
    email = models.EmailField("Email", unique=True)
    phone = models.CharField("Số điện thoại", max_length=20, blank=True)
    company = models.CharField("Công ty", max_length=255, blank=True)
    segment = models.CharField(
        "Phân khúc", max_length=20, choices=SEGMENT_CHOICES, default="new"
    )
    notes = models.TextField("Ghi chú CRM", blank=True)
    ai_summary = models.TextField("AI Summary", blank=True)
    ai_recommendation = models.TextField("AI Recommendation", blank=True)
    ai_email_subject = models.CharField("AI Email Subject", max_length=255, blank=True)
    ai_email_body = models.TextField("AI Email Body", blank=True)
    ai_last_run_at = models.DateTimeField("Lần chạy AI gần nhất", null=True, blank=True)
    created_at = models.DateTimeField("Ngày tạo", auto_now_add=True)
    updated_at = models.DateTimeField("Cập nhật", auto_now=True)

    class Meta:
        verbose_name = "Khách hàng"
        verbose_name_plural = "Khách hàng"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    @property
    def total_spent(self):
        value = self.orders.aggregate(total=models.Sum("total_amount"))["total"]
        return value or Decimal("0")

    @property
    def order_count(self):
        return self.orders.count()

    def segment_badge(self):
        css = {
            "new": "crm-badge crm-badge--blue",
            "regular": "crm-badge crm-badge--green",
            "vip": "crm-badge crm-badge--gold",
            "risk": "crm-badge crm-badge--red",
        }.get(self.segment, "crm-badge")
        return format_html(
            '<span class="{}">{}</span>', css, self.get_segment_display()
        )

    segment_badge.short_description = "Phân khúc"

    def total_spent_display(self):
        return f"{self.total_spent:,.0f} ₫"

    total_spent_display.short_description = "Tổng chi tiêu"


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
        "Trạng thái", max_length=20, choices=STATUS_CHOICES, default="pending"
    )
    description = models.TextField("Mô tả đơn hàng", blank=True)
    created_at = models.DateTimeField("Ngày tạo", auto_now_add=True)

    class Meta:
        verbose_name = "Đơn hàng"
        verbose_name_plural = "Đơn hàng"
        ordering = ["-created_at", "-pk"]

    def __str__(self):
        return f"{self.order_code} – {self.customer.name}"

    def status_badge(self):
        css = (
            "crm-badge crm-badge--green"
            if self.status == "completed"
            else "crm-badge crm-badge--amber"
        )
        return format_html(
            '<span class="{}">{}</span>', css, self.get_status_display()
        )

    status_badge.short_description = "Trạng thái"

    def amount_display(self):
        return f"{self.total_amount:,.0f} ₫"

    amount_display.short_description = "Tổng tiền"


class AIAnalysisLog(models.Model):
    ACTION_CHOICES = [
        ("analysis", "Phân tích khách hàng"),
        ("email", "Gợi ý phản hồi email"),
        ("report", "Báo cáo CRM"),
    ]

    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="ai_logs",
        null=True,
        blank=True,
        verbose_name="Khách hàng",
    )
    action_type = models.CharField(
        "Loại thao tác", max_length=20, choices=ACTION_CHOICES
    )
    model_name = models.CharField("Model AI", max_length=100, blank=True)
    output_text = models.TextField("Kết quả AI", blank=True)
    created_at = models.DateTimeField("Thời gian", auto_now_add=True)

    class Meta:
        verbose_name = "Nhật ký AI"
        verbose_name_plural = "Nhật ký AI"
        ordering = ["-created_at"]

    def __str__(self):
        target = self.customer.name if self.customer else "CRM"
        return (
            f"{target} – {self.get_action_type_display()} – "
            f"{self.created_at:%d/%m/%Y %H:%M}"
        )


customer_content_panels = [
    MultiFieldPanel(
        [
            FieldPanel("name"),
            FieldPanel("email"),
            FieldPanel("phone"),
            FieldPanel("company"),
        ],
        heading="Thông tin khách hàng",
    ),
    MultiFieldPanel(
        [
            FieldPanel("segment"),
            FieldPanel("notes"),
        ],
        heading="CRM",
    ),
]

customer_ai_panels = [
    MultiFieldPanel(
        [
            FieldPanel("ai_summary"),
            FieldPanel("ai_recommendation"),
        ],
        heading="Phân tích khách hàng",
    ),
    MultiFieldPanel(
        [
            FieldPanel("ai_email_subject"),
            FieldPanel("ai_email_body"),
        ],
        heading="Gợi ý email",
    ),
    FieldPanel("ai_last_run_at"),
]

Customer.edit_handler = TabbedInterface(
    [
        ObjectList(customer_content_panels, heading="Khách hàng"),
        ObjectList(customer_ai_panels, heading="AI"),
    ]
)
