from django.db.models import Q, Sum
from wagtail.models import Page

from crm.models import AIAnalysisLog, Customer, Order


class HomePage(Page):
    subpage_types = []

    def get_context(self, request):
        context = super().get_context(request)
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

        context.update(
            {
                "metrics": {
                    "customer_count": Customer.objects.count(),
                    "order_count": Order.objects.count(),
                    "revenue": Order.objects.filter(status="completed").aggregate(
                        total=Sum("total_amount")
                    )["total"]
                    or 0,
                    "vip_count": Customer.objects.filter(segment="vip").count(),
                    "risk_count": Customer.objects.filter(segment="risk").count(),
                    "pending_count": Order.objects.filter(status="pending").count(),
                    "ai_count": AIAnalysisLog.objects.count(),
                },
                "customers": customers[:8],
                "orders": Order.objects.select_related("customer")[:6],
                "ai_logs": AIAnalysisLog.objects.select_related("customer")[:6],
                "segments": Customer.SEGMENT_CHOICES,
                "q": q,
                "selected_segment": segment,
            }
        )
        return context
