# crm/models.py

from decimal import Decimal
from django.conf import settings
from django.db import models
from django.db.models import Sum
from django.urls import reverse
from django.utils.html import format_html
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet, SnippetViewSetGroup


# ──────────────────────────────────────────────
# Model: Customer (Hồ sơ Khách hàng)
# ──────────────────────────────────────────────
class Customer(models.Model):
    CUSTOMER_TYPE_CHOICES = [
        ("b2c", "Cá nhân (B2C)"),
        ("b2b", "Doanh nghiệp (B2B)"),
    ]

    TIER_CHOICES = [
        ("standard", "Standard"),
        ("silver", "Silver"),
        ("gold", "Gold"),
        ("platinum", "Platinum"),
    ]

    name = models.CharField("Tên khách hàng", max_length=255)
    email = models.EmailField("Email", unique=True)
    phone = models.CharField("Số điện thoại", max_length=20, blank=True)
    company = models.CharField("Công ty / Đơn vị", max_length=255, blank=True)
    address = models.CharField("Địa chỉ", max_length=255, blank=True)
    customer_type = models.CharField(
        "Phân loại", max_length=10, choices=CUSTOMER_TYPE_CHOICES, default="b2c"
    )
    tier = models.CharField(
        "Hạng thành viên", max_length=20, choices=TIER_CHOICES, default="standard"
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="managed_customers",
        verbose_name="Nhân viên phụ trách",
    )
    created_at = models.DateTimeField("Ngày tạo", auto_now_add=True)

    panels = [
        MultiFieldPanel(
            [
                FieldPanel("name"),
                FieldPanel("company"),
                FieldPanel("email"),
                FieldPanel("phone"),
                FieldPanel("address"),
            ],
            heading="Thông tin liên hệ",
        ),
        MultiFieldPanel(
            [
                FieldPanel("customer_type"),
                FieldPanel("tier"),
                FieldPanel("assigned_to"),
            ],
            heading="Phân hạng & Phân công",
        ),
    ]

    class Meta:
        verbose_name = "Khách hàng"
        verbose_name_plural = "Khách hàng"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.company})" if self.company else self.name

    @property
    def total_spent(self):
        """Tổng chi tiêu từ các đơn hàng đã hoàn thành."""
        res = self.orders.filter(status="completed").aggregate(total=Sum("total_amount"))["total"]
        return res or Decimal("0")

    @property
    def completed_orders_count(self):
        return self.orders.filter(status="completed").count()

    @property
    def pending_orders_count(self):
        return self.orders.filter(status="pending").count()

    @property
    def active_tickets_count(self):
        return self.support_tickets.exclude(status__in=["resolved", "closed"]).count()

    @property
    def tier_progress(self):
        """Tính toán tiến độ thăng hạng thành viên kế tiếp."""
        spent = self.total_spent
        if self.tier == "platinum":
            return {"current": spent, "target": spent, "percent": 100, "next": "Hạng tối đa"}
        elif self.tier == "gold":
            target = Decimal("50000000")
            percent = min(100, int((spent / target) * 100))
            return {"current": spent, "target": target, "percent": percent, "next": "Platinum (50.000.000đ)"}
        elif self.tier == "silver":
            target = Decimal("20000000")
            percent = min(100, int((spent / target) * 100))
            return {"current": spent, "target": target, "percent": percent, "next": "Gold (20.000.000đ)"}
        else:
            target = Decimal("5000000")
            percent = min(100, int((spent / target) * 100))
            return {"current": spent, "target": target, "percent": percent, "next": "Silver (5.000.000đ)"}

    def update_tier_automatically(self):
        """Tự động nâng hạng khách hàng dựa trên tổng doanh số đã hoàn thành."""
        spent = self.total_spent
        new_tier = "standard"
        if spent >= Decimal("50000000"):
            new_tier = "platinum"
        elif spent >= Decimal("20000000"):
            new_tier = "gold"
        elif spent >= Decimal("5000000"):
            new_tier = "silver"

        if self.tier != new_tier:
            old_tier_display = self.get_tier_display()
            self.tier = new_tier
            self.save(update_fields=["tier"])
            # Tự động ghi nhật ký tương tác
            Interaction.objects.create(
                customer=self,
                user=self.assigned_to,
                interaction_type="note",
                summary=f"⭐ Tự động thăng hạng thẻ: {old_tier_display} ➔ {self.get_tier_display()}",
                content=f"Khách hàng đã tích lũy doanh số hoàn thành đạt {spent:,.0f} VNĐ, hệ thống CRM tự động thăng hạng thẻ thành viên.",
            )
            return True
        return False

    def profile_360_button(self):
        url = reverse("crm_customer_360", args=[self.pk])
        return format_html(
            '<a href="{}" style="font-weight:700; padding:4px 10px; border-radius:6px; background:#4f46e5; color:#fff; text-decoration:none; display:inline-flex; align-items:center; gap:4px; font-size:12px;">👁️ Hồ sơ 360°</a>',
            url,
        )

    profile_360_button.short_description = "Hồ sơ 360°"


# ──────────────────────────────────────────────
# Model: Lead (Khách hàng tiềm năng)
# ──────────────────────────────────────────────
class Lead(models.Model):
    SOURCE_CHOICES = [
        ("website", "Website / Form"),
        ("social", "Mạng xã hội (FB/TikTok)"),
        ("referral", "Khách hàng giới thiệu"),
        ("event", "Sự kiện / Hội chợ"),
        ("cold_call", "Telesale / Trực tiếp"),
        ("other", "Nguồn khác"),
    ]

    STATUS_CHOICES = [
        ("new", "Mới tiếp cận (New)"),
        ("contacted", "Đã liên hệ (Contacted)"),
        ("qualified", "Đạt điều kiện (Qualified)"),
        ("proposal", "Báo giá / Đàm phán (Proposal)"),
        ("won", "Chốt thành công (Won)"),
        ("lost", "Thất bại (Lost)"),
    ]

    name = models.CharField("Họ và tên", max_length=255)
    company = models.CharField("Công ty / Đơn vị", max_length=255, blank=True)
    email = models.EmailField("Email", blank=True)
    phone = models.CharField("Số điện thoại", max_length=20)
    source = models.CharField(
        "Nguồn tiếp cận", max_length=20, choices=SOURCE_CHOICES, default="website"
    )
    status = models.CharField(
        "Giai đoạn phễu", max_length=20, choices=STATUS_CHOICES, default="new"
    )
    estimated_value = models.DecimalField(
        "Giá trị kỳ vọng (VNĐ)", max_digits=12, decimal_places=2, default=0
    )
    notes = models.TextField("Ghi chú nhu cầu", blank=True)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="managed_leads",
        verbose_name="Nhân viên phụ trách",
    )
    is_converted = models.BooleanField("Đã chuyển đổi thành khách hàng", default=False)
    converted_customer = models.ForeignKey(
        Customer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="origin_leads",
        verbose_name="Khách hàng chuyển đổi",
    )
    converted_at = models.DateTimeField("Thời gian chuyển đổi", null=True, blank=True)
    created_at = models.DateTimeField("Ngày tiếp nhận", auto_now_add=True)

    panels = [
        MultiFieldPanel(
            [
                FieldPanel("name"),
                FieldPanel("company"),
                FieldPanel("email"),
                FieldPanel("phone"),
            ],
            heading="Thông tin người liên hệ",
        ),
        MultiFieldPanel(
            [
                FieldPanel("source"),
                FieldPanel("status"),
                FieldPanel("estimated_value"),
                FieldPanel("assigned_to"),
                FieldPanel("notes"),
            ],
            heading="Trạng thái cơ hội bán hàng",
        ),
        MultiFieldPanel(
            [
                FieldPanel("is_converted", read_only=True),
                FieldPanel("converted_customer", read_only=True),
                FieldPanel("converted_at", read_only=True),
            ],
            heading="Tiến trình chuyển đổi",
        ),
    ]

    class Meta:
        verbose_name = "Khách hàng tiềm năng (Lead)"
        verbose_name_plural = "Khách hàng tiềm năng (Leads)"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} [{self.get_status_display()}]"

    def convert_action(self):
        if self.is_converted and self.converted_customer:
            url = reverse("crm_customer_360", args=[self.converted_customer.pk])
            return format_html(
                '<a href="{}" style="color:#059669; font-weight:700; text-decoration:none; font-size:12px;">✅ Đã chuyển đổi ({})</a>',
                url,
                self.converted_customer.name,
            )
        url = reverse("crm_convert_lead", args=[self.pk])
        return format_html(
            '<a href="{}" style="font-weight:700; padding:4px 10px; border-radius:6px; background:#10b981; color:#fff; text-decoration:none; display:inline-flex; align-items:center; gap:4px; font-size:12px;">⚡ Chuyển đổi</a>',
            url,
        )

    convert_action.short_description = "Hành động CRM"


# ──────────────────────────────────────────────
# Model: Product (Danh mục Sản phẩm & Dịch vụ)
# ──────────────────────────────────────────────
class Product(models.Model):
    CATEGORY_CHOICES = [
        ("software", "Phần mềm & Dịch vụ"),
        ("course", "Khóa học đào tạo"),
        ("hardware", "Thiết bị công nghệ"),
        ("accessory", "Phụ kiện & Khác"),
    ]

    STATUS_CHOICES = [
        ("active", "Đang kinh doanh"),
        ("out_of_stock", "Tạm hết hàng"),
        ("discontinued", "Ngừng kinh doanh"),
    ]

    name = models.CharField("Tên sản phẩm / Dịch vụ", max_length=255)
    sku = models.CharField("Mã sản phẩm (SKU)", max_length=50, unique=True)
    category = models.CharField(
        "Danh mục", max_length=20, choices=CATEGORY_CHOICES, default="software"
    )
    price = models.DecimalField("Giá bán (VNĐ)", max_digits=12, decimal_places=2, default=0)
    status = models.CharField("Trạng thái", max_length=20, choices=STATUS_CHOICES, default="active")
    description = models.TextField("Mô tả sản phẩm", blank=True)
    created_at = models.DateTimeField("Ngày tạo", auto_now_add=True)

    panels = [
        FieldPanel("name"),
        FieldPanel("sku"),
        FieldPanel("category"),
        FieldPanel("price"),
        FieldPanel("status"),
        FieldPanel("description"),
    ]

    class Meta:
        verbose_name = "Sản phẩm"
        verbose_name_plural = "Sản phẩm"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.sku})"


# ──────────────────────────────────────────────
# Model: Order (Đơn hàng)
# ──────────────────────────────────────────────
class Order(ClusterableModel):
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
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="managed_orders",
        verbose_name="Nhân viên phụ trách",
    )
    notes = models.TextField("Ghi chú đơn hàng", blank=True)
    created_at = models.DateTimeField("Ngày tạo", auto_now_add=True)

    panels = [
        MultiFieldPanel(
            [
                FieldPanel("customer"),
                FieldPanel("order_code"),
                FieldPanel("assigned_to"),
                FieldPanel("status"),
            ],
            heading="Thông tin đơn hàng",
        ),
        MultiFieldPanel(
            [
                FieldPanel("payment_method"),
                FieldPanel("shipping_provider"),
                FieldPanel("total_amount"),
                FieldPanel("notes"),
            ],
            heading="Thanh toán & Giao vận",
        ),
        InlinePanel("items", label="Chi tiết sản phẩm / Dịch vụ"),
    ]

    class Meta:
        verbose_name = "Đơn hàng"
        verbose_name_plural = "Đơn hàng"
        ordering = ["-pk"]

    def __str__(self):
        return f"{self.order_code} – {self.customer.name}"


# ──────────────────────────────────────────────
# Model: OrderItem (Chi tiết mặt hàng trong đơn)
# ──────────────────────────────────────────────
class OrderItem(models.Model):
    order = ParentalKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="Đơn hàng",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="order_items",
        verbose_name="Sản phẩm",
    )
    quantity = models.PositiveIntegerField("Số lượng", default=1)
    unit_price = models.DecimalField("Đơn giá", max_digits=12, decimal_places=2, default=0)

    panels = [
        FieldPanel("product"),
        FieldPanel("quantity"),
        FieldPanel("unit_price"),
    ]

    class Meta:
        verbose_name = "Chi tiết mặt hàng"
        verbose_name_plural = "Chi tiết mặt hàng"

    @property
    def subtotal(self):
        return self.quantity * self.unit_price

    def __str__(self):
        return f"{self.product.name} (x{self.quantity})"


# ──────────────────────────────────────────────
# Model: Interaction (Nhật ký chăm sóc & tương tác)
# ──────────────────────────────────────────────
class Interaction(models.Model):
    TYPE_CHOICES = [
        ("call", "Cuộc gọi điện"),
        ("email", "Gửi email"),
        ("meeting", "Gặp trực tiếp / Demo"),
        ("note", "Ghi chú nội bộ"),
    ]

    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="interactions",
        verbose_name="Khách hàng",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="crm_interactions",
        verbose_name="Nhân viên thực hiện",
    )
    interaction_type = models.CharField(
        "Loại tương tác",
        max_length=20,
        choices=TYPE_CHOICES,
        default="call",
    )
    summary = models.CharField("Tiêu đề / Tóm tắt", max_length=255)
    content = models.TextField("Chi tiết trao đổi", blank=True)
    interaction_date = models.DateTimeField("Thời gian thực hiện", auto_now_add=True)
    follow_up_date = models.DateField("Lịch hẹn tiếp theo", null=True, blank=True)

    panels = [
        FieldPanel("customer"),
        FieldPanel("user"),
        FieldPanel("interaction_type"),
        FieldPanel("summary"),
        FieldPanel("content"),
        FieldPanel("follow_up_date"),
    ]

    class Meta:
        verbose_name = "Nhật ký tương tác"
        verbose_name_plural = "Nhật ký tương tác"
        ordering = ["-interaction_date"]

    def __str__(self):
        return f"{self.get_interaction_type_display()}: {self.summary} - {self.customer.name}"


# ──────────────────────────────────────────────
# Model: SupportTicket (Phiếu hỗ trợ sau bán)
# ──────────────────────────────────────────────
class SupportTicket(models.Model):
    PRIORITY_CHOICES = [
        ("low", "Thấp"),
        ("medium", "Trung bình"),
        ("high", "Cao"),
        ("urgent", "Khẩn cấp"),
    ]

    STATUS_CHOICES = [
        ("open", "Tiếp nhận mới"),
        ("in_progress", "Đang xử lý"),
        ("pending", "Chờ khách phản hồi"),
        ("resolved", "Đã giải quyết"),
        ("closed", "Đã đóng"),
    ]

    ticket_code = models.CharField("Mã phiếu", max_length=50, unique=True)
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="support_tickets",
        verbose_name="Khách hàng",
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="support_tickets",
        verbose_name="Đơn hàng liên quan",
    )
    subject = models.CharField("Tiêu đề sự cố", max_length=255)
    description = models.TextField("Mô tả chi tiết")
    priority = models.CharField(
        "Mức độ ưu tiên", max_length=20, choices=PRIORITY_CHOICES, default="medium"
    )
    status = models.CharField(
        "Trạng thái", max_length=20, choices=STATUS_CHOICES, default="open"
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_tickets",
        verbose_name="Nhân viên xử lý",
    )
    created_at = models.DateTimeField("Ngày tiếp nhận", auto_now_add=True)
    resolved_at = models.DateTimeField("Ngày giải quyết", null=True, blank=True)

    panels = [
        FieldPanel("ticket_code"),
        FieldPanel("customer"),
        FieldPanel("order"),
        FieldPanel("subject"),
        FieldPanel("description"),
        FieldPanel("priority"),
        FieldPanel("status"),
        FieldPanel("assigned_to"),
        FieldPanel("resolved_at"),
    ]

    class Meta:
        verbose_name = "Phiếu hỗ trợ (Ticket)"
        verbose_name_plural = "Phiếu hỗ trợ (Tickets)"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.ticket_code} - {self.subject}"


# ──────────────────────────────────────────────
# Model: RevenueForecast (Dự báo doanh thu chuỗi thời gian AI)
# ──────────────────────────────────────────────
class RevenueForecast(models.Model):
    forecast_date = models.DateField("Ngày dự báo", db_index=True)
    predicted_revenue = models.DecimalField("Doanh thu dự báo (VNĐ)", max_digits=14, decimal_places=2)
    lower_bound = models.DecimalField("Cận dưới tin cậy (VNĐ)", max_digits=14, decimal_places=2, default=0)
    upper_bound = models.DecimalField("Cận trên tin cậy (VNĐ)", max_digits=14, decimal_places=2, default=0)
    model_name = models.CharField("Mô hình AI", max_length=100, default="Ridge Time-Series Regression")
    mae = models.FloatField("Sai số tuyệt đối TB (MAE)", default=0.0)
    r2_score = models.FloatField("Độ chính xác (R² Score)", default=0.0)
    notes = models.TextField("Ghi chú phân tích xu hướng", blank=True)
    created_at = models.DateTimeField("Thời gian huấn luyện", auto_now=True)

    panels = [
        FieldPanel("forecast_date"),
        FieldPanel("predicted_revenue"),
        FieldPanel("lower_bound"),
        FieldPanel("upper_bound"),
        FieldPanel("model_name"),
        FieldPanel("mae"),
        FieldPanel("r2_score"),
        FieldPanel("notes"),
    ]

    class Meta:
        verbose_name = "Dự báo doanh thu AI"
        verbose_name_plural = "Dự báo doanh thu AI"
        ordering = ["forecast_date"]

    def __str__(self):
        return f"{self.forecast_date}: {self.predicted_revenue:,.0f} VNĐ"


# ──────────────────────────────────────────────
# Model: CustomerSegment (Phân loại & Phân khúc Khách hàng AI - RFM + KMeans)
# ──────────────────────────────────────────────
class CustomerSegment(models.Model):
    CHURN_RISK_CHOICES = [
        ("low", "Thấp (< 25%)"),
        ("medium", "Trung bình (25% - 50%)"),
        ("high", "Cao (> 50%)"),
    ]

    customer = models.OneToOneField(
        Customer,
        on_delete=models.CASCADE,
        related_name="ai_segment",
        verbose_name="Khách hàng",
    )
    recency_days = models.IntegerField("Số ngày chưa mua hàng (Recency)", default=0)
    frequency = models.IntegerField("Số đơn hàng hoàn thành (Frequency)", default=0)
    monetary = models.DecimalField("Tổng chi tiêu (Monetary)", max_digits=14, decimal_places=2, default=0)
    r_score = models.IntegerField("Điểm R (1-5)", default=1)
    f_score = models.IntegerField("Điểm F (1-5)", default=1)
    m_score = models.IntegerField("Điểm M (1-5)", default=1)
    rfm_score = models.CharField("Mã RFM", max_length=10, default="111")
    cluster_id = models.IntegerField("Mã cụm K-Means", default=0)
    segment_label = models.CharField("Phân khúc khách hàng", max_length=100, default="Tiềm năng")
    churn_risk = models.CharField("Rủi ro rời bỏ", max_length=20, choices=CHURN_RISK_CHOICES, default="low")
    churn_probability = models.FloatField("Xác suất rời bỏ (0-1)", default=0.1)
    suggested_action = models.TextField("Chiến lược gợi ý", blank=True)
    updated_at = models.DateTimeField("Ngày phân loại", auto_now=True)

    panels = [
        FieldPanel("customer"),
        FieldPanel("segment_label"),
        FieldPanel("rfm_score"),
        FieldPanel("recency_days"),
        FieldPanel("frequency"),
        FieldPanel("monetary"),
        FieldPanel("churn_risk"),
        FieldPanel("churn_probability"),
        FieldPanel("suggested_action"),
    ]

    class Meta:
        verbose_name = "Phân khúc khách hàng AI"
        verbose_name_plural = "Phân khúc khách hàng AI"
        ordering = ["-monetary"]

    def __str__(self):
        return f"{self.customer.name} - [{self.segment_label}]"


# ──────────────────────────────────────────────
# Wagtail Snippet ViewSets & Registration
# ──────────────────────────────────────────────
class CustomerViewSet(SnippetViewSet):
    model = Customer
    icon = "user"
    menu_label = "Khách hàng"
    menu_name = "customers"
    list_display = [
        "name",
        "company",
        "phone",
        "tier",
        "assigned_to",
        "profile_360_button",
    ]
    list_filter = ["tier", "customer_type", "assigned_to"]
    search_fields = ["name", "email", "phone", "company"]


class LeadViewSet(SnippetViewSet):
    model = Lead
    icon = "pick"
    menu_label = "Khách hàng tiềm năng"
    menu_name = "leads"
    list_display = [
        "name",
        "company",
        "phone",
        "source",
        "status",
        "estimated_value",
        "assigned_to",
        "convert_action",
    ]
    list_filter = ["status", "source", "assigned_to", "is_converted"]
    search_fields = ["name", "company", "email", "phone"]


class ProductViewSet(SnippetViewSet):
    model = Product
    icon = "snippet"
    menu_label = "Sản phẩm & Dịch vụ"
    menu_name = "products"
    list_display = ["sku", "name", "category", "price", "status"]
    list_filter = ["category", "status"]
    search_fields = ["sku", "name"]


class OrderViewSet(SnippetViewSet):
    model = Order
    icon = "form"
    menu_label = "Đơn hàng"
    menu_name = "orders"
    list_display = [
        "order_code",
        "customer",
        "total_amount",
        "payment_method",
        "shipping_provider",
        "status",
        "assigned_to",
    ]
    list_filter = ["status", "payment_method", "shipping_provider", "assigned_to"]
    search_fields = ["order_code", "customer__name"]


class InteractionViewSet(SnippetViewSet):
    model = Interaction
    icon = "mail"
    menu_label = "Nhật ký tương tác"
    menu_name = "interactions"
    list_display = [
        "summary",
        "customer",
        "interaction_type",
        "user",
        "interaction_date",
        "follow_up_date",
    ]
    list_filter = ["interaction_type", "user"]
    search_fields = ["summary", "content", "customer__name"]


class SupportTicketViewSet(SnippetViewSet):
    model = SupportTicket
    icon = "help"
    menu_label = "Phiếu hỗ trợ (Tickets)"
    menu_name = "support_tickets"
    list_display = [
        "ticket_code",
        "subject",
        "customer",
        "priority",
        "status",
        "assigned_to",
        "created_at",
    ]
    list_filter = ["priority", "status", "assigned_to"]
    search_fields = ["ticket_code", "subject", "customer__name"]


class CustomerSegmentViewSet(SnippetViewSet):
    model = CustomerSegment
    icon = "group"
    menu_label = "Phân khúc KH (AI)"
    menu_name = "customer_segments"
    list_display = [
        "customer",
        "segment_label",
        "rfm_score",
        "recency_days",
        "frequency",
        "monetary",
        "churn_risk",
    ]
    list_filter = ["segment_label", "churn_risk"]
    search_fields = ["customer__name", "segment_label", "rfm_score"]


class RevenueForecastViewSet(SnippetViewSet):
    model = RevenueForecast
    icon = "date"
    menu_label = "Dự báo Doanh thu (AI)"
    menu_name = "revenue_forecasts"
    list_display = [
        "forecast_date",
        "predicted_revenue",
        "lower_bound",
        "upper_bound",
        "model_name",
        "mae",
        "r2_score",
    ]
    list_filter = ["model_name"]


class CRMViewSetGroup(SnippetViewSetGroup):
    items = (
        CustomerViewSet,
        LeadViewSet,
        OrderViewSet,
        ProductViewSet,
        InteractionViewSet,
        SupportTicketViewSet,
        CustomerSegmentViewSet,
        RevenueForecastViewSet,
    )
    menu_icon = "folder-open-inverse"
    menu_label = "Quản lý CRM"
    menu_name = "crm"
    menu_order = 200


register_snippet(CRMViewSetGroup)
