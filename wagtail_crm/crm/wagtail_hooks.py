from django.urls import path, reverse
from wagtail import hooks
from wagtail.admin.menu import MenuItem

from crm import views


class CRMReportMenuItem(MenuItem):
    def is_shown(self, request):
        return request.user.has_perm("crm.view_order")


@hooks.register("register_admin_urls")
def register_admin_urls():
    return [path("crm/ai-report/", views.ai_report, name="crm_ai_report")]


@hooks.register("register_admin_menu_item")
def register_ai_report_menu_item():
    return CRMReportMenuItem(
        "Phân tích AI",
        reverse("crm_ai_report"),
        name="crm-ai-report",
        icon_name="site",
        order=850,
    )