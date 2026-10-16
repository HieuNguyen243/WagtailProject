# crm/views.py

import json
from decimal import Decimal
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import (
    Customer,
    CustomerSegment,
    Interaction,
    Lead,
    Order,
    OrderItem,
    Product,
    RevenueForecast,
    SupportTicket,
)
from .ai_engine import run_all_ai_pipeline, run_customer_segmentation, run_revenue_forecasting

User = get_user_model()


# ──────────────────────────────────────────────
# 2. Phễu Bán Hàng Trực Quan (Interactive Kanban Pipeline)
# ──────────────────────────────────────────────
@login_required
def sales_pipeline_view(request):
    """
    Kanban Board phễu bán hàng dành cho Khách hàng tiềm năng (Leads).
    Hiển thị trực quan theo từng giai đoạn, tính tổng giá trị deal và hỗ trợ chuyển đổi nhanh.
    """
    assigned_filter = request.GET.get("assigned_to")
    search_query = request.GET.get("q", "").strip()

    leads_qs = Lead.objects.select_related("assigned_to", "converted_customer").all()

    if assigned_filter:
        leads_qs = leads_qs.filter(assigned_to_id=assigned_filter)
    if search_query:
        leads_qs = leads_qs.filter(name__icontains=search_query) | leads_qs.filter(company__icontains=search_query)

    STAGES_CONFIG = [
        {"key": "new", "label": "Mới tiếp cận", "color": "#3b82f6", "badge_bg": "#eff6ff"},
        {"key": "contacted", "label": "Đã liên hệ", "color": "#0ea5e9", "badge_bg": "#f0f9ff"},
        {"key": "qualified", "label": "Đạt điều kiện", "color": "#8b5cf6", "badge_bg": "#f5f3ff"},
        {"key": "proposal", "label": "Báo giá / Đàm phán", "color": "#f59e0b", "badge_bg": "#fffbeb"},
        {"key": "won", "label": "Chốt thành công", "color": "#10b981", "badge_bg": "#ecfdf5"},
        {"key": "lost", "label": "Thất bại", "color": "#ef4444", "badge_bg": "#fef2f2"},
    ]

    columns = []
    total_pipeline_value = Decimal("0")
    total_leads_count = leads_qs.count()

    for stage in STAGES_CONFIG:
        stage_leads = [l for l in leads_qs if l.status == stage["key"]]
        stage_value = sum(l.estimated_value for l in stage_leads)
        if stage["key"] not in ["lost"]:
            total_pipeline_value += stage_value

        columns.append({
            "key": stage["key"],
            "label": stage["label"],
            "color": stage["color"],
            "badge_bg": stage["badge_bg"],
            "leads": stage_leads,
            "count": len(stage_leads),
            "total_value": stage_value,
        })

    sales_users = User.objects.filter(is_staff=True).order_by("first_name", "username")

    context = {
        "columns": columns,
        "total_leads_count": total_leads_count,
        "total_pipeline_value": total_pipeline_value,
        "sales_users": sales_users,
        "selected_assigned": assigned_filter,
        "search_query": search_query,
        "page_title": "Phễu Bán Hàng Trực Quan (Sales Kanban)",
    }
    return render(request, "crm/pipeline.html", context)


# ──────────────────────────────────────────────
# 3. API Di Chuyển Giai Đoạn Lead (AJAX Drag/Click)
# ──────────────────────────────────────────────
@login_required
@require_POST
def api_update_lead_stage(request, lead_id):
    lead = get_object_or_404(Lead, pk=lead_id)
    new_status = request.POST.get("new_status")

    valid_statuses = [choice[0] for choice in Lead.STATUS_CHOICES]
    if new_status not in valid_statuses:
        return JsonResponse({"success": False, "error": "Trạng thái không hợp lệ."}, status=400)

    old_status_display = lead.get_status_display()
    lead.status = new_status
    lead.save(update_fields=["status"])

    return JsonResponse({
        "success": True,
        "lead_id": lead.id,
        "new_status": new_status,
        "old_status_display": old_status_display,
        "new_status_display": lead.get_status_display(),
        "is_won": new_status == "won",
        "is_converted": lead.is_converted,
    })


# ──────────────────────────────────────────────
# 4. Hồ Sơ Khách Hàng 360° (Customer 360 Profile)
# ──────────────────────────────────────────────
@login_required
def customer_360_view(request, customer_id):
    customer = get_object_or_404(
        Customer.objects.select_related("assigned_to"),
        pk=customer_id,
    )
    orders = customer.orders.prefetch_related("items__product").order_by("-id")
    interactions = customer.interactions.select_related("user").order_by("-interaction_date")
    tickets = customer.support_tickets.select_related("assigned_to", "order").order_by("-created_at")
    origin_leads = customer.origin_leads.all()
    active_products = Product.objects.filter(status="active").order_by("name")

    # Xử lý thông báo toast nếu có
    saved_flag = request.GET.get("saved")
    if saved_flag == "interaction":
        messages.success(request, "Đã ghi nhận tương tác mới thành công!")
    elif saved_flag == "order":
        messages.success(request, "Đã tạo đơn hàng mới cho khách hàng thành công!")

    context = {
        "customer": customer,
        "orders": orders,
        "interactions": interactions,
        "tickets": tickets,
        "origin_leads": origin_leads,
        "active_products": active_products,
        "tier_progress": customer.tier_progress,
        "page_title": f"Hồ sơ 360° – {customer.name}",
    }
    return render(request, "crm/customer_360.html", context)


# ──────────────────────────────────────────────
# 5. Ghi Nhanh Tương Tác / Nhật Ký CSKH
# ──────────────────────────────────────────────
@login_required
@require_POST
def quick_interaction_view(request, customer_id):
    customer = get_object_or_404(Customer, pk=customer_id)

    interaction_type = request.POST.get("interaction_type", "call")
    summary = request.POST.get("summary", "").strip()
    content = request.POST.get("content", "").strip()
    follow_up_str = request.POST.get("follow_up_date", "").strip()

    follow_up_date = None
    if follow_up_str:
        try:
            follow_up_date = timezone.datetime.strptime(follow_up_str, "%Y-%m-%d").date()
        except ValueError:
            pass

    if summary:
        Interaction.objects.create(
            customer=customer,
            user=request.user,
            interaction_type=interaction_type,
            summary=summary,
            content=content,
            follow_up_date=follow_up_date,
        )
        messages.success(request, "Đã thêm nhật ký tương tác thành công!")

    return redirect(reverse("crm_customer_360", args=[customer.id]) + "?tab=interactions&saved=interaction")


# ──────────────────────────────────────────────
# 6. Chuyển Đổi Lead Thành Khách Hàng (Lead Conversion)
# ──────────────────────────────────────────────
@login_required
def convert_lead_view(request, lead_id):
    lead = get_object_or_404(Lead, pk=lead_id)

    # Nếu lead đã được chuyển đổi từ trước
    if lead.is_converted and lead.converted_customer:
        messages.info(request, f"Lead này đã được chuyển đổi thành khách hàng {lead.converted_customer.name} trước đó.")
        return redirect("crm_customer_360", customer_id=lead.converted_customer.id)

    # Kiểm tra xem có khách hàng nào trùng SĐT hoặc Email không
    matched_customer = None
    if lead.email:
        matched_customer = Customer.objects.filter(email=lead.email).first()
    if not matched_customer and lead.phone:
        matched_customer = Customer.objects.filter(phone=lead.phone).first()

    if request.method == "POST":
        action_mode = request.POST.get("action_mode", "create_new")
        create_initial_order = request.POST.get("create_initial_order") == "1"

        if action_mode == "link_existing" and matched_customer:
            target_customer = matched_customer
        else:
            cust_name = request.POST.get("name", lead.name).strip()
            cust_email = request.POST.get("email", lead.email).strip() or f"lead_{lead.id}@crm.internal"
            cust_phone = request.POST.get("phone", lead.phone).strip()
            cust_company = request.POST.get("company", lead.company).strip()

            target_customer = Customer.objects.create(
                name=cust_name,
                email=cust_email,
                phone=cust_phone,
                company=cust_company,
                assigned_to=lead.assigned_to or request.user,
                customer_type="b2b" if cust_company else "b2c",
            )

        # Cập nhật trạng thái của Lead
        lead.is_converted = True
        lead.converted_customer = target_customer
        lead.status = "won"
        lead.converted_at = timezone.now()
        lead.save(update_fields=["is_converted", "converted_customer", "status", "converted_at"])

        # Tạo nhật ký tương tác ghi nhận sự kiện chuyển đổi
        Interaction.objects.create(
            customer=target_customer,
            user=request.user,
            interaction_type="meeting",
            summary=f"🚀 Chuyển đổi thành công từ Lead #{lead.id}: {lead.name}",
            content=f"Khách hàng tiềm năng từ nguồn '{lead.get_source_display()}' đã được chuyển đổi chính thức. Nhu cầu ban đầu: {lead.notes}",
        )

        # Tùy chọn tạo ngay đơn hàng đầu tiên
        if create_initial_order and lead.estimated_value > 0:
            order_count_today = Order.objects.count() + 1
            new_code = f"ORD-CONV-{lead.id:03d}-{order_count_today:03d}"
            Order.objects.create(
                customer=target_customer,
                order_code=new_code,
                total_amount=lead.estimated_value,
                status="pending",
                assigned_to=lead.assigned_to or request.user,
                notes=f"Đơn hàng khởi tạo tự động từ quy trình chốt Sale Lead: {lead.notes}",
            )

        # Kích hoạt kiểm tra thăng hạng thẻ
        target_customer.update_tier_automatically()

        messages.success(request, f"🎉 Chuyển đổi thành công! Khách hàng '{target_customer.name}' đã sẵn sàng trong hệ thống CRM.")
        return redirect("crm_customer_360", customer_id=target_customer.id)

    context = {
        "lead": lead,
        "matched_customer": matched_customer,
        "page_title": f"Chuyển đổi Khách hàng tiềm năng: {lead.name}",
    }
    return render(request, "crm/convert_lead.html", context)


# ──────────────────────────────────────────────
# 7. Tạo Đơn Hàng Nhanh Cho Khách Hàng (Từ 360 View)
# ──────────────────────────────────────────────
@login_required
@require_POST
def quick_create_order_view(request, customer_id):
    customer = get_object_or_404(Customer, pk=customer_id)

    product_id = request.POST.get("product_id")
    quantity = int(request.POST.get("quantity", 1))
    payment_method = request.POST.get("payment_method", "MB_eBanking")
    shipping_provider = request.POST.get("shipping_provider", "SPX_Express")
    notes = request.POST.get("notes", "").strip()

    product = get_object_or_404(Product, pk=product_id)

    order_num = Order.objects.count() + 1
    order_code = f"ORD-FAST-{customer.id:03d}-{order_num:04d}"

    order = Order.objects.create(
        customer=customer,
        order_code=order_code,
        payment_method=payment_method,
        shipping_provider=shipping_provider,
        status="pending",
        assigned_to=customer.assigned_to or request.user,
        notes=notes,
        total_amount=Decimal("0"),
    )

    OrderItem.objects.create(
        order=order,
        product=product,
        quantity=quantity,
        unit_price=product.price,
    )

    # Tính toán tổng tiền
    order.total_amount = product.price * quantity
    order.save(update_fields=["total_amount"])

    # Tự động ghi nhật ký tương tác
    Interaction.objects.create(
        customer=customer,
        user=request.user,
        interaction_type="note",
        summary=f"🛒 Tạo đơn hàng mới {order.order_code}",
        content=f"Đơn hàng được tạo nhanh gồm {quantity}x {product.name}. Tổng tiền: {order.total_amount:,.0f} VNĐ.",
    )

    messages.success(request, f"Đã tạo thành công đơn hàng {order.order_code}!")
    return redirect(reverse("crm_customer_360", args=[customer.id]) + "?tab=orders&saved=order")


# ──────────────────────────────────────────────
# 6. Quản trị & Trực quan hóa Mô hình AI Cục bộ
# ──────────────────────────────────────────────
@login_required
def ai_models_dashboard_view(request):
    """
    Dashboard quản trị và hiển thị kết quả từ 2 mô hình Machine Learning:
    1. Time-series Revenue Forecasting (Ridge Regression 30 ngày)
    2. Customer RFM & K-Means Clustering & Churn Risk
    Hỗ trợ nút bấm huấn luyện lại (Re-train) và xuất dữ liệu sang Apache Superset.
    """
    if request.method == "POST":
        res = run_all_ai_pipeline()
        if res.get("success"):
            messages.success(
                request,
                "⚡ Đã huấn luyện và cập nhật thành công toàn bộ kết quả AI vào CSDL (Bảng RevenueForecast & CustomerSegment)!"
            )
        else:
            messages.warning(
                request,
                f"Đã chạy pipeline với lưu ý: Dự báo={res.get('forecasting', {}).get('success')}, Phân khúc={res.get('segmentation', {}).get('success')}"
            )
        return redirect(reverse("crm_ai_models_dashboard"))

    # Lấy dữ liệu dự báo doanh thu
    forecast_qs = RevenueForecast.objects.all().order_by("forecast_date")
    total_forecast_revenue = sum(f.predicted_revenue for f in forecast_qs)
    latest_forecast = forecast_qs.first()

    # Lấy lịch sử doanh thu thực tế 30 ngày gần nhất để ghép biểu đồ so sánh
    history_orders = Order.objects.filter(status="completed").order_by("created_at")
    history_daily = {}
    for o in history_orders:
        d_str = str(o.created_at.date())
        history_daily[d_str] = history_daily.get(d_str, 0.0) + float(o.total_amount)

    history_dates = sorted(history_daily.keys())[-30:] if history_daily else []
    history_values = [history_daily[d] for d in history_dates]

    forecast_dates = [str(f.forecast_date) for f in forecast_qs]
    forecast_values = [float(f.predicted_revenue) for f in forecast_qs]
    lower_bounds = [float(f.lower_bound) for f in forecast_qs]
    upper_bounds = [float(f.upper_bound) for f in forecast_qs]

    # Lấy phân khúc khách hàng
    segments_qs = CustomerSegment.objects.select_related("customer").order_by("-monetary")
    total_customers = segments_qs.count()

    # Thống kê phân bố
    segment_counts = {}
    churn_counts = {"low": 0, "medium": 0, "high": 0}
    for s in segments_qs:
        segment_counts[s.segment_label] = segment_counts.get(s.segment_label, 0) + 1
        churn_counts[s.churn_risk] = churn_counts.get(s.churn_risk, 0) + 1

    chart_payload = {
        "history_dates": history_dates,
        "history_values": history_values,
        "forecast_dates": forecast_dates,
        "forecast_values": forecast_values,
        "lower_bounds": lower_bounds,
        "upper_bounds": upper_bounds,
        "segment_labels": list(segment_counts.keys()),
        "segment_counts": list(segment_counts.values()),
        "churn_labels": ["Rủi ro thấp (<25%)", "Trung bình (25-50%)", "Nguy cơ cao (>50%)"],
        "churn_counts": [churn_counts.get("low", 0), churn_counts.get("medium", 0), churn_counts.get("high", 0)],
    }

    context = {
        "page_title": "🤖 Quản trị & Trực quan hóa Mô hình AI",
        "forecast_qs": forecast_qs[:10],
        "total_forecast_revenue": total_forecast_revenue,
        "forecast_count": forecast_qs.count(),
        "latest_forecast": latest_forecast,
        "segments_qs": segments_qs,
        "total_customers": total_customers,
        "churn_counts": churn_counts,
        "chart_json": json.dumps(chart_payload, ensure_ascii=False),
    }
    return render(request, "crm/ai_models_dashboard.html", context)


# ──────────────────────────────────────────────
# 7. Nhúng Apache Superset BI Dashboard vào Wagtail
# ──────────────────────────────────────────────
@login_required
def superset_dashboard_view(request):
    """
    Giao diện nhúng trực tiếp Apache Superset Dashboard vào Wagtail Admin.
    Hỗ trợ tùy chỉnh URL dashboard, chế độ xem toàn màn hình (Fullscreen)
    và hướng dẫn kết nối các bảng CSDL AI đã tạo.
    """
    default_url = getattr(
        settings,
        "SUPERSET_DASHBOARD_URL",
        "http://localhost:8088/superset/dashboard/11/?standalone=1"
    )

    if request.method == "POST":
        action = request.POST.get("action", "")
        if action == "reset":
            request.session.pop("custom_superset_url", None)
            messages.success(request, "Đã đặt lại URL Apache Superset Dashboard mặc định.")
            return redirect(reverse("crm_superset_dashboard"))

        new_url = request.POST.get("superset_url", "").strip()
        if new_url:
            request.session["custom_superset_url"] = new_url
            messages.success(request, f"Đã lưu URL Apache Superset Dashboard: {new_url}")
            return redirect(reverse("crm_superset_dashboard"))

    superset_url = request.session.get("custom_superset_url") or default_url

    # Số liệu tóm tắt trong DB sẵn sàng cho Superset
    revenue_rows = RevenueForecast.objects.count()
    segment_rows = CustomerSegment.objects.count()
    order_rows = Order.objects.count()

    context = {
        "page_title": "📊 Apache Superset BI Dashboard",
        "superset_url": superset_url,
        "revenue_rows": revenue_rows,
        "segment_rows": segment_rows,
        "order_rows": order_rows,
        "db_name": "db.sqlite3",
    }
    response = render(request, "crm/superset_embed.html", context)
    response["X-Frame-Options"] = "SAMEORIGIN"
    response["Content-Security-Policy"] = (
        "frame-src 'self' http://localhost:8088 http://127.0.0.1:8088 https://localhost:8088; "
        "connect-src 'self' http://localhost:8088 http://127.0.0.1:8088; "
        "img-src 'self' data: blob: http://localhost:8088 http://127.0.0.1:8088;"
    )
    return response
