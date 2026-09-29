# crm/wagtail_hooks.py
from django.urls import path, reverse
from wagtail import hooks
from wagtail.admin.menu import MenuItem
from crm.views import ai_sales_report_view


@hooks.register("register_admin_urls")
def register_ai_report_url():
    return [
        path("ai-report/", ai_sales_report_view, name="ai_sales_report"),
    ]


@hooks.register("register_admin_menu_item")
def register_ai_report_menu_item():
    return MenuItem(
        label="Phân tích AI",
        url=reverse("ai_sales_report"),
        icon_name="clipboard-list",
        order=201,
    )
