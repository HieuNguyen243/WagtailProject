import json
import os
from decimal import Decimal
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.db.models import Avg, Count, Sum

from crm.models import Customer, Order


class AIAnalysisError(Exception):
    pass


def build_crm_report():
    order_totals = Order.objects.aggregate(
        order_count=Count("id"),
        revenue=Sum("total_amount"),
        average_order=Avg("total_amount"),
    )
    status_labels = dict(Order.STATUS_CHOICES)
    payment_labels = dict(Order.PAYMENT_METHOD_CHOICES)
    shipping_labels = dict(Order.SHIPPING_PROVIDER_CHOICES)

    return {
        "customer_count": Customer.objects.count(),
        "order_count": order_totals["order_count"],
        "total_revenue_vnd": str(order_totals["revenue"] or Decimal("0.00")),
        "average_order_vnd": str(order_totals["average_order"] or Decimal("0.00")),
        "orders_by_status": {
            status_labels.get(row["status"], row["status"]): row["count"]
            for row in Order.objects.values("status").annotate(count=Count("id"))
        },
        "orders_by_payment_method": {
            payment_labels.get(row["payment_method"], row["payment_method"]): row["count"]
            for row in Order.objects.values("payment_method").annotate(count=Count("id"))
        },
        "orders_by_shipping_provider": {
            shipping_labels.get(row["shipping_provider"], row["shipping_provider"]): row["count"]
            for row in Order.objects.values("shipping_provider").annotate(count=Count("id"))
        },
    }


def request_ai_analysis(report, prompt=""):
    api_key = os.getenv("AI_API_KEY")
    if not api_key:
        raise AIAnalysisError("Chưa cấu hình AI_API_KEY trên máy chủ.")

    api_url = os.getenv("AI_API_URL", "https://api.openai.com/v1/chat/completions")
    model = os.getenv("AI_MODEL", "gpt-4o-mini")
    user_prompt = prompt or "Phân tích tình hình CRM và đề xuất các hành động phù hợp."
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Bạn là chuyên gia phân tích CRM. Trả lời bằng tiếng Việt, "
                    "chỉ dựa trên dữ liệu được cung cấp, nêu rõ giới hạn của dữ liệu "
                    "và không tự suy diễn số liệu."
                ),
            },
            {
                "role": "user",
                "content": f"Yêu cầu: {user_prompt}\n\nDữ liệu CRM tổng hợp:\n"
                f"{json.dumps(report, ensure_ascii=False, indent=2)}",
            },
        ],
        "temperature": 0.3,
    }
    request = Request(
        api_url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))
        content = result["choices"][0]["message"]["content"]
    except HTTPError as exc:
        raise AIAnalysisError(f"Dịch vụ AI trả về lỗi HTTP {exc.code}.") from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise AIAnalysisError("Không thể kết nối đến dịch vụ AI.") from exc
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        raise AIAnalysisError("Dịch vụ AI trả về dữ liệu không hợp lệ.") from exc

    if not isinstance(content, str) or not content.strip():
        raise AIAnalysisError("Dịch vụ AI không trả về nội dung phân tích.")
    return content.strip()