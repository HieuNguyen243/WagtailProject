from django.templatetags.static import static
from django.urls import path, reverse
from django.utils.html import format_html

from wagtail import hooks
from wagtail.admin import widgets as wagtailadmin_widgets
from wagtail.admin.ui.components import Component
from wagtail.admin.viewsets.base import ViewSet, ViewSetGroup

from .models import AIAnalysisLog, Customer, Order
from .views import (
    ai_workspace,
    analyze_customer,
    crm_dashboard,
    crm_report,
    email_customer,
    export_customers,
    generate_report,
)
from wagtail.snippets.views.snippets import SnippetViewSet


class CRMDashboardViewSet(ViewSet):
    name = "crm-dashboard"
    url_prefix = "crm-dashboard"
    url_namespace = "crm_admin"
    menu_label = "Tổng quan"
    icon = "dashboard"
    menu_order = 10

    def get_urlpatterns(self):
        return [
            path("", crm_dashboard, name="dashboard"),
            path("customer/<int:pk>/", ai_workspace, name="workspace"),
            path("customer/<int:pk>/analyze/", analyze_customer, name="analyze"),
            path("customer/<int:pk>/email/", email_customer, name="email"),
            path("report/", crm_report, name="report"),
            path("report/generate/", generate_report, name="report_generate"),
            path("customers/export/", export_customers, name="export"),
        ]


class CRMReportViewSet(ViewSet):
    name = "crm-report"
    url_prefix = "crm-report"
    url_namespace = "crm_reports"
    menu_label = "Báo cáo AI"
    icon = "doc-full"
    menu_order = 40

    def get_urlpatterns(self):
        return [
            path("", crm_report, name="index"),
            path("generate/", generate_report, name="generate"),
        ]


class CustomerViewSet(SnippetViewSet):
    model = Customer
    icon = "user"
    menu_label = "Khách hàng"
    menu_name = "customers"
    menu_order = 20
    list_display = [
        "name",
        "company",
        "email",
        "segment_badge",
        "total_spent_display",
        "order_count",
        "created_at",
    ]
    search_fields = ["name", "email", "phone", "company"]
    list_filter = ["segment", "created_at"]


class OrderViewSet(SnippetViewSet):
    model = Order
    icon = "list-ul"
    menu_label = "Đơn hàng"
    menu_name = "orders"
    menu_order = 30
    list_display = [
        "order_code",
        "customer",
        "amount_display",
        "payment_method",
        "shipping_provider",
        "status_badge",
        "created_at",
    ]
    search_fields = ["order_code", "customer__name", "customer__email"]
    list_filter = ["status", "payment_method", "shipping_provider", "created_at"]


class AIAnalysisLogViewSet(SnippetViewSet):
    model = AIAnalysisLog
    icon = "history"
    menu_label = "Nhật ký AI"
    menu_name = "ai-logs"
    menu_order = 50
    list_display = ["customer", "action_type", "model_name", "created_at"]
    search_fields = ["customer__name", "customer__email", "output_text"]
    list_filter = ["action_type", "created_at"]


class CRMViewSetGroup(ViewSetGroup):
    menu_label = "Quản lý CRM"
    menu_icon = "folder-open-inverse"
    menu_order = 200
    items = (
        CRMDashboardViewSet(),
        CustomerViewSet(),
        OrderViewSet(),
        CRMReportViewSet(),
        AIAnalysisLogViewSet(),
    )


@hooks.register("register_admin_viewset")
def register_crm_viewset_group():
    return CRMViewSetGroup()


@hooks.register("register_snippet_listing_buttons")
def customer_ai_buttons(snippet, user, next_url=None):
    if isinstance(snippet, Customer):
        yield wagtailadmin_widgets.ListingButton(
            "✦ AI",
            reverse("crm_admin:workspace", kwargs={"pk": snippet.pk}),
            priority=10,
        )


@hooks.register("insert_global_admin_css")
def crm_admin_css():
    return format_html(
        '<link rel="stylesheet" href="{}">',
        static("css/wagtail_admin_crm.css"),
    )


@hooks.register("insert_global_admin_js")
def crm_admin_js():
    return format_html(
        '<script src="{}" defer></script>',
        static("js/wagtail_admin_crm.js"),
    )


class CRMHomepagePanel(Component):
    order = 80

    def render_html(self, parent_context):
        from .views import _metrics

        metrics = _metrics()
        dashboard_url = reverse("crm_admin:dashboard")
        report_url = reverse("crm_reports:index")

        return format_html(
            '<section class="crm-home-card">'
            '<div class="crm-home-card__head">'
            '<div>'
            '<span class="crm-eyebrow">AI CRM · WAGTAIL</span>'
            '<h2>Trung tâm quản trị khách hàng</h2>'
            '<p>Một giao diện thống nhất cho dữ liệu, AI và vận hành CRM.</p>'
            '</div>'
            '<div class="crm-home-card__actions">'
            '<a class="crm-home-card__button" href="{}">Dashboard</a>'
            '<a class="crm-home-card__button crm-home-card__button--light" href="{}">Báo cáo AI</a>'
            '</div>'
            '</div>'
            '<div class="crm-home-card__stats">'
            '<div><small>Khách hàng</small><strong>{}</strong></div>'
            '<div><small>Đơn hàng</small><strong>{}</strong></div>'
            '<div><small>Doanh thu</small><strong>{:,.0f} ₫</strong></div>'
            '<div><small>VIP</small><strong>{}</strong></div>'
            '</div>'
            '</section>',
            dashboard_url,
            report_url,
            metrics["customer_count"],
            metrics["order_count"],
            metrics["revenue"],
            metrics["vip_count"],
        )


@hooks.register("construct_homepage_panels")
def add_crm_home_panel(request, panels):
    panels.append(CRMHomepagePanel())
