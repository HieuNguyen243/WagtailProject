import json
import os
from decimal import Decimal

from django.utils import timezone

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover
    OpenAI = None


SEGMENT_LABELS = {
    "new": "Khách mới",
    "regular": "Khách thường xuyên",
    "vip": "Khách VIP",
    "risk": "Có nguy cơ rời bỏ",
}


def _model_name():
    return os.getenv("OPENAI_MODEL", "gpt-5.6-luna")


def _client():
    key = os.getenv("OPENAI_API_KEY")
    if not key or OpenAI is None:
        return None
    return OpenAI(api_key=key)


def _customer_payload(customer):
    orders = list(customer.orders.all().order_by("-created_at", "-pk"))
    return {
        "name": customer.name,
        "email": customer.email,
        "phone": customer.phone,
        "company": customer.company,
        "segment": customer.segment,
        "notes": customer.notes,
        "total_spent": float(customer.total_spent or 0),
        "order_count": len(orders),
        "orders": [
            {
                "code": o.order_code,
                "amount": float(o.total_amount),
                "status": o.get_status_display(),
                "payment": o.get_payment_method_display(),
            }
            for o in orders[:10]
        ],
    }


def _fallback_analysis(data):
    total = Decimal(str(data["total_spent"]))
    count = int(data["order_count"])
    if total >= 20_000_000 or count >= 5:
        segment = "vip"
    elif count >= 2:
        segment = "regular"
    elif count == 0:
        segment = "new"
    else:
        segment = "risk" if data["notes"] and "không" in data["notes"].lower() else "regular"

    summary = (
        f"{data['name']} hiện có {count} đơn hàng với tổng giá trị {total:,.0f} VND. "
        f"Phân khúc hiện tại: {SEGMENT_LABELS[segment]}."
    )
    recommendation = (
        "Ưu tiên chăm sóc cá nhân hóa và chương trình khách hàng thân thiết."
        if segment == "vip"
        else "Theo dõi tần suất mua và chủ động gợi ý sản phẩm phù hợp."
        if segment == "regular"
        else "Gửi lời chào và hướng dẫn mua hàng để kích hoạt khách hàng."
        if segment == "new"
        else "Chủ động liên hệ, hỏi nguyên nhân giảm tương tác và đưa ra ưu đãi phù hợp."
    )
    return {"segment": segment, "summary": summary, "recommendation": recommendation}


def analyze_customer(customer):
    data = _customer_payload(customer)
    prompt = f"""
Bạn là chuyên viên CRM AI. Phân tích dữ liệu khách hàng sau và trả về JSON thuần:
{{
  "segment": "new | regular | vip | risk",
  "summary": "tóm tắt ngắn bằng tiếng Việt",
  "recommendation": "đề xuất hành động cụ thể bằng tiếng Việt"
}}

Dữ liệu:
{json.dumps(data, ensure_ascii=False, indent=2)}
"""
    client = _client()
    if client is None:
        return {**_fallback_analysis(data), "model": "fallback-demo", "timestamp": timezone.now()}

    try:
        response = client.responses.create(model=_model_name(), input=prompt)
        raw = response.output_text.strip().replace("```json", "").replace("```", "").strip()
        result = json.loads(raw)
        if result.get("segment") not in SEGMENT_LABELS:
            raise ValueError("AI returned invalid segment")
        return {**result, "model": _model_name(), "timestamp": timezone.now()}
    except Exception:
        return {**_fallback_analysis(data), "model": "fallback-demo", "timestamp": timezone.now()}


def generate_email_reply(customer):
    data = _customer_payload(customer)
    prompt = f"""
Tạo một email chăm sóc khách hàng bằng tiếng Việt dựa trên dữ liệu sau.
Trả JSON thuần:
{{"subject":"tiêu đề email", "body":"nội dung email"}}

{json.dumps(data, ensure_ascii=False, indent=2)}
"""
    client = _client()
    if client is None:
        return {
            "subject": f"Chăm sóc khách hàng – {customer.name}",
            "body": (
                f"Kính chào {customer.name},\n\n"
                "Cảm ơn anh/chị đã đồng hành cùng chúng tôi. "
                "Đội ngũ CRM muốn gửi lời hỏi thăm và hỗ trợ anh/chị với các nhu cầu sắp tới.\n\n"
                "Trân trọng,\nĐội ngũ CRM"
            ),
            "model": "fallback-demo",
        }

    try:
        response = client.responses.create(model=_model_name(), input=prompt)
        raw = response.output_text.strip().replace("```json", "").replace("```", "").strip()
        result = json.loads(raw)
        return {**result, "model": _model_name()}
    except Exception:
        return {
            "subject": f"Chăm sóc khách hàng – {customer.name}",
            "body": "Kính chào anh/chị, cảm ơn anh/chị đã tin tưởng sản phẩm và dịch vụ của chúng tôi.",
            "model": "fallback-demo",
        }


def generate_crm_report(metrics):
    prompt = f"""
Viết báo cáo CRM ngắn bằng tiếng Việt từ dữ liệu:
{json.dumps(metrics, ensure_ascii=False, indent=2)}
Gồm 3 phần: tổng quan, điểm cần chú ý, hành động đề xuất.
"""
    client = _client()
    if client is None:
        return (
            f"Tổng quan: {metrics['customer_count']} khách hàng, {metrics['order_count']} đơn hàng, "
            f"doanh thu hoàn thành {metrics['revenue']:,.0f} VND.\n\n"
            f"Điểm cần chú ý: {metrics['risk_count']} khách có nguy cơ rời bỏ và "
            f"{metrics['pending_count']} đơn đang xử lý.\n\n"
            "Hành động đề xuất: ưu tiên chăm sóc nhóm VIP/Risk và xử lý các đơn đang chờ."
        ), "fallback-demo"
    try:
        response = client.responses.create(model=_model_name(), input=prompt)
        return response.output_text.strip(), _model_name()
    except Exception:
        return "Không thể tạo báo cáo AI lúc này.", "fallback-demo"
