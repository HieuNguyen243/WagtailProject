# crm/wagtail_hooks.py

from django.urls import path, reverse
from wagtail import hooks
from wagtail.admin.menu import MenuItem

from crm.views import (
    ai_models_dashboard_view,
    api_update_lead_stage,
    convert_lead_view,
    customer_360_view,
    quick_create_order_view,
    quick_interaction_view,
    sales_pipeline_view,
    superset_dashboard_view,
)


@hooks.register("register_admin_urls")
def register_crm_admin_urls():
    return [
        path("ai-models/", ai_models_dashboard_view, name="crm_ai_models_dashboard"),
        path("superset/", superset_dashboard_view, name="crm_superset_dashboard"),
        path("pipeline/", sales_pipeline_view, name="crm_sales_pipeline"),
        path("api/leads/<int:lead_id>/update-stage/", api_update_lead_stage, name="crm_api_update_lead_stage"),
        path("customers/<int:customer_id>/360/", customer_360_view, name="crm_customer_360"),
        path("customers/<int:customer_id>/quick-interaction/", quick_interaction_view, name="crm_quick_interaction"),
        path("customers/<int:customer_id>/quick-order/", quick_create_order_view, name="crm_quick_create_order"),
        path("leads/<int:lead_id>/convert/", convert_lead_view, name="crm_convert_lead"),
    ]


@hooks.register("register_admin_menu_item")
def register_pipeline_menu_item():
    return MenuItem(
        label="🎯 Phễu Bán Hàng",
        url=reverse("crm_sales_pipeline"),
        icon_name="tasks",
        order=198,
    )


@hooks.register("register_admin_menu_item")
def register_ai_models_menu_item():
    return MenuItem(
        label="🤖 Dự Báo & Phân Khúc AI",
        url=reverse("crm_ai_models_dashboard"),
        icon_name="chart-line",
        order=201,
    )


@hooks.register("register_admin_menu_item")
def register_superset_menu_item():
    return MenuItem(
        label="📊 Superset BI Dashboard",
        url=reverse("crm_superset_dashboard"),
        icon_name="view",
        order=202,
    )
