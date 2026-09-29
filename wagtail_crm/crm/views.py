from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .models import AIAnalysisLog, Customer, Order
from .services.ai import analyze_customer, generate_crm_report, generate_email_reply


def _metrics():
    revenue = (
        Order.objects.filter(status="completed")
        .aggregate(total=Sum("total_amount"))["total"]
        or Decimal("0")
    )
    return {
        "customer_count": Customer.objects.count(),
        "order_count": Order.objects.count(),
        "revenue": revenue,
        "vip_count": Customer.objects.filter(segment="vip").count(),
        "risk_count": Customer.objects.filter(segment="risk").count(),
        "pending_count": Order.objects.filter(status="pending").count(),
        "ai_count": AIAnalysisLog.objects.count(),
    }


def _run_analysis(customer):
    result = analyze_customer(customer)
    customer.segment = result["segment"]
    customer.ai_summary = result["summary"]
    customer.ai_recommendation = result["recommendation"]
    customer.ai_last_run_at = result["timestamp"]
    customer.save(
        update_fields=[
            "segment",
            "ai_summary",
            "ai_recommendation",
            "ai_last_run_at",
            "updated_at",
        ]
    )
    AIAnalysisLog.objects.create(
        customer=customer,
        action_type="analysis",
        model_name=result["model"],
        output_text=(
            f"Phân khúc: {customer.get_segment_display()}\n\n"
            f"Tóm tắt: {result['summary']}\n\n"
            f"Khuyến nghị: {result['recommendation']}"
        ),
    )
    return result


def _run_email(customer):
    result = generate_email_reply(customer)
    customer.ai_email_subject = result["subject"]
    customer.ai_email_body = result["body"]
    customer.save(update_fields=["ai_email_subject", "ai_email_body", "updated_at"])
    AIAnalysisLog.objects.create(
        customer=customer,
        action_type="email",
        model_name=result["model"],
        output_text=f"{result['subject']}\n\n{result['body']}",
    )
    return result


@login_required
def crm_dashboard(request):
    context = {
        "metrics": _metrics(),
        "recent_customers": Customer.objects.all()[:8],
        "recent_orders": Order.objects.select_related("customer")[:8],
        "recent_logs": AIAnalysisLog.objects.select_related("customer")[:8],
    }
    return render(request, "crm/admin/dashboard.html", context)


@login_required
def ai_workspace(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    context = {
        "customer": customer,
        "orders": customer.orders.all()[:12],
        "logs": customer.ai_logs.all()[:8],
    }
    return render(request, "crm/admin/ai_workspace.html", context)


@login_required
def analyze_customer(request, pk):
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")
    customer = get_object_or_404(Customer, pk=pk)
    _run_analysis(customer)
    messages.success(request, f"Đã phân tích AI cho {customer.name}.")
    return redirect(reverse("crm_admin:workspace", kwargs={"pk": customer.pk}))


@login_required
def email_customer(request, pk):
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")
    customer = get_object_or_404(Customer, pk=pk)
    _run_email(customer)
    messages.success(request, f"Đã tạo gợi ý email cho {customer.name}.")
    return redirect(reverse("crm_admin:workspace", kwargs={"pk": customer.pk}))


@login_required
def generate_report(request):
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")
    metrics = _metrics()
    report, model = generate_crm_report({**metrics, "revenue": float(metrics["revenue"])})
    AIAnalysisLog.objects.create(action_type="report", model_name=model, output_text=report)
    request.session["crm_ai_report"] = report
    messages.success(request, "Đã tạo báo cáo CRM bằng AI.")
    return redirect(reverse("crm_reports:index"))


@login_required
def crm_report(request):
    latest_report = (
        AIAnalysisLog.objects.filter(action_type="report")
        .order_by("-created_at")
        .first()
    )
    context = {
        "metrics": _metrics(),
        "latest_report": latest_report,
    }
    return render(request, "crm/admin/report.html", context)


@login_required
def export_customers(request):
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="crm_customers.csv"'
    response.write("Tên,Email,Điện thoại,Công ty,Phân khúc,Tổng chi tiêu,Số đơn\n")
    for customer in Customer.objects.all():
        row = [
            customer.name,
            customer.email,
            customer.phone,
            customer.company,
            customer.get_segment_display(),
            f"{customer.total_spent:,.0f}",
            customer.order_count,
        ]
        response.write(",".join('"%s"' % str(v).replace('"', '""') for v in row) + "\n")
    return response


def public_customer_list(request):
    q = request.GET.get("q", "").strip()
    segment = request.GET.get("segment", "").strip()
    customers = Customer.objects.all()
    if q:
        customers = customers.filter(
            Q(name__icontains=q)
            | Q(email__icontains=q)
            | Q(company__icontains=q)
        )
    if segment:
        customers = customers.filter(segment=segment)
    return render(
        request,
        "crm/public/customer_list.html",
        {
            "customers": customers[:50],
            "q": q,
            "segment": segment,
            "segments": Customer.SEGMENT_CHOICES,
        },
    )


def public_customer_detail(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    return render(
        request,
        "crm/public/customer_detail.html",
        {
            "customer": customer,
            "orders": customer.orders.all()[:20],
            "logs": customer.ai_logs.all()[:10],
        },
    )


def public_order_list(request):
    orders = Order.objects.select_related("customer")[:50]
    return render(request, "crm/public/order_list.html", {"orders": orders})
