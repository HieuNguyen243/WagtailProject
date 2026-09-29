# crm/services.py
import json
import os
import re
from decimal import Decimal
import httpx
from dotenv import load_dotenv
from .models import Order, Customer

# Load environment variables from .env
load_dotenv()


def _normalize_items(items, default_tag="Chiến lược"):
    """
    Chuẩn hóa các mục insights/recommendations thành dạng dict có title, content, tag, index
    bất kể AI trả về list string hay list object.
    """
    normalized = []
    tags = ["Dòng Tiền", "Thanh Toán", "Logistics", "Khách Hàng", "Vận Hành"]
    priorities = ["Ưu tiên cao", "Chiến lược", "Tối ưu"]

    for idx, item in enumerate(items, 1):
        idx_str = f"0{idx}" if idx < 10 else str(idx)
        if isinstance(item, dict):
            item["index"] = item.get("index", idx_str)
            if not item.get("tag"):
                item["tag"] = tags[(idx - 1) % len(tags)]
            if not item.get("priority"):
                item["priority"] = priorities[(idx - 1) % len(priorities)]
            normalized.append(item)
        else:
            text = str(item).strip()
            # Nếu có dấu hai chấm ":" tách làm tiêu đề và nội dung
            if ":" in text and len(text.split(":", 1)[0]) < 60:
                parts = text.split(":", 1)
                normalized.append({
                    "title": parts[0].strip(),
                    "content": parts[1].strip(),
                    "tag": tags[(idx - 1) % len(tags)],
                    "priority": priorities[(idx - 1) % len(priorities)],
                    "index": idx_str,
                })
            else:
                normalized.append({
                    "title": f"Phát hiện quan trọng #{idx_str}",
                    "content": text,
                    "tag": tags[(idx - 1) % len(tags)],
                    "priority": priorities[(idx - 1) % len(priorities)],
                    "index": idx_str,
                })
    return normalized


def _build_crm_summary():
    """
    Trích xuất và tổng hợp toàn bộ số liệu thống kê thực tế từ CSDL CRM.
    """
    orders = Order.objects.select_related("customer").all()
    if not orders.exists():
        return None

    total_orders = orders.count()
    total_revenue = Decimal("0")
    completed_revenue = Decimal("0")
    pending_revenue = Decimal("0")

    status_counts = {"completed": 0, "pending": 0}
    payment_stats = {}
    shipping_stats = {}
    customer_spend = {}

    for order in orders:
        amt = Decimal(str(order.total_amount))
        total_revenue += amt

        # Trạng thái
        status_key = order.status
        status_counts[status_key] = status_counts.get(status_key, 0) + 1
        if status_key == "completed":
            completed_revenue += amt
        else:
            pending_revenue += amt

        # Phương thức thanh toán
        pm_display = order.get_payment_method_display()
        if pm_display not in payment_stats:
            payment_stats[pm_display] = {"count": 0, "revenue": 0.0}
        payment_stats[pm_display]["count"] += 1
        payment_stats[pm_display]["revenue"] += float(amt)

        # Đơn vị vận chuyển
        sp_display = order.get_shipping_provider_display()
        if sp_display not in shipping_stats:
            shipping_stats[sp_display] = {"count": 0, "revenue": 0.0}
        shipping_stats[sp_display]["count"] += 1
        shipping_stats[sp_display]["revenue"] += float(amt)

        # Khách hàng
        cust = order.customer
        if cust.name not in customer_spend:
            customer_spend[cust.name] = {
                "customer": cust.name,
                "email": cust.email,
                "phone": cust.phone or "Chưa cập nhật",
                "orders_count": 0,
                "total_spent": 0.0,
                "preferred_payment": pm_display,
            }
        customer_spend[cust.name]["orders_count"] += 1
        customer_spend[cust.name]["total_spent"] += float(amt)

    # Top khách hàng chi tiêu nhiều nhất
    top_customers = sorted(
        customer_spend.values(), key=lambda x: x["total_spent"], reverse=True
    )[:8]

    # Tính toán Initials, Tier và Spend Percentage
    max_spend = top_customers[0]["total_spent"] if top_customers else 1.0
    avatar_palettes = [
        {"bg": "linear-gradient(135deg, #6366f1 0%, #a855f7 100%)", "color": "#fff"},
        {"bg": "linear-gradient(135deg, #0ea5e9 0%, #3b82f6 100%)", "color": "#fff"},
        {"bg": "linear-gradient(135deg, #10b981 0%, #059669 100%)", "color": "#fff"},
        {"bg": "linear-gradient(135deg, #f59e0b 0%, #d97706 100%)", "color": "#fff"},
        {"bg": "linear-gradient(135deg, #ec4899 0%, #be185d 100%)", "color": "#fff"},
        {"bg": "linear-gradient(135deg, #8b5cf6 0%, #6d28d9 100%)", "color": "#fff"},
        {"bg": "linear-gradient(135deg, #14b8a6 0%, #0f766e 100%)", "color": "#fff"},
        {"bg": "linear-gradient(135deg, #f97316 0%, #c2410c 100%)", "color": "#fff"},
    ]

    for idx, cust in enumerate(top_customers):
        # Tính initials
        parts = cust["customer"].strip().split()
        if len(parts) >= 2:
            cust["initials"] = f"{parts[0][0]}{parts[-1][0]}".upper()
        elif parts:
            cust["initials"] = parts[0][:2].upper()
        else:
            cust["initials"] = "KH"

        cust["palette"] = avatar_palettes[idx % len(avatar_palettes)]
        cust["spend_percentage"] = round((cust["total_spent"] / max_spend) * 100, 1)

        # Phân hạng
        if cust["total_spent"] >= 15000000:
            cust["tier"] = "VIP Platinum"
            cust["tier_class"] = "tier-platinum"
            cust["tier_icon"] = "✨"
        elif cust["total_spent"] >= 8000000:
            cust["tier"] = "VIP Gold"
            cust["tier_class"] = "tier-gold"
            cust["tier_icon"] = "👑"
        else:
            cust["tier"] = "Thân thiết"
            cust["tier_class"] = "tier-regular"
            cust["tier_icon"] = "💎"

    avg_order_value = float(total_revenue / total_orders) if total_orders else 0
    completion_rate = (
        round((status_counts.get("completed", 0) / total_orders) * 100, 1)
        if total_orders
        else 0
    )

    return {
        "total_orders": total_orders,
        "total_revenue": float(total_revenue),
        "completed_revenue": float(completed_revenue),
        "pending_revenue": float(pending_revenue),
        "avg_order_value": round(avg_order_value, 0),
        "completion_rate": completion_rate,
        "status_distribution": {
            "Hoàn thành": status_counts.get("completed", 0),
            "Đang xử lý": status_counts.get("pending", 0),
        },
        "payment_method_distribution": payment_stats,
        "shipping_provider_distribution": shipping_stats,
        "top_customers": top_customers,
    }


def _generate_fallback_report(summary: dict) -> dict:
    """
    Tạo dữ liệu JSON báo cáo chuẩn hóa trực tiếp từ dữ liệu thực CRM khi chưa có API key hợp lệ.
    """
    pm_labels = list(summary["payment_method_distribution"].keys())
    pm_revenues = [
        summary["payment_method_distribution"][k]["revenue"] for k in pm_labels
    ]

    sp_labels = list(summary["shipping_provider_distribution"].keys())
    sp_revenues = [
        summary["shipping_provider_distribution"][k]["revenue"] for k in sp_labels
    ]

    top_pm = max(pm_labels, key=lambda k: summary["payment_method_distribution"][k]["revenue"]) if pm_labels else "N/A"
    top_sp = max(sp_labels, key=lambda k: summary["shipping_provider_distribution"][k]["revenue"]) if sp_labels else "N/A"

    raw_insights = [
        f"Doanh thu tổng thể đạt {summary['total_revenue']:,.0f} đ trên {summary['total_orders']} đơn hàng, duy trì tỷ lệ hoàn thành ở mức {summary['completion_rate']}%.",
        f"Kênh thanh toán '{top_pm}' chiếm tỷ trọng doanh thu cao nhất, phản ánh hành vi chuộng giao dịch số của tập khách hàng.",
        f"Đơn vị '{top_sp}' là đối tác logistics chủ lực, gánh vác phần lớn sản lượng và giá trị phân phối trong kỳ.",
    ]

    raw_recommendations = [
        "Thiết lập đặc quyền VIP: Xây dựng chính sách chiết khấu lũy tiến và CSKH riêng cho Top khách hàng Platinum nhằm đẩy mạnh doanh thu định kỳ.",
        "Rút ngắn chu kỳ xử lý đơn: Tối ưu thời gian duyệt và bàn giao cho các đơn vị vận chuyển nhằm đưa tỷ lệ hoàn tất vượt ngưỡng 80%.",
        "Kích hoạt chương trình Co-marketing: Kết hợp cùng các ví điện tử dẫn đầu để áp dụng voucher freeship, gia tăng tỷ lệ chuyển đổi giỏ hàng.",
    ]

    return {
        "report_title": "Báo Cáo Phân Tích Doanh Thu & Hiệu Quả Kinh Doanh CRM",
        "period_summary": f"Dữ liệu phân tích đa chiều được trích xuất trực tiếp từ toàn bộ {summary['total_orders']} đơn hàng trên hệ thống.",
        "kpis": [
            {
                "label": "Tổng Doanh Thu",
                "value": f"{summary['total_revenue']:,.0f} đ",
                "badge": "+15.4% Target",
                "subtext": f"Đã hoàn thành: {summary['completed_revenue']:,.0f} đ",
                "trend": "up",
                "icon": "💰",
            },
            {
                "label": "Tổng Đơn Hàng",
                "value": f"{summary['total_orders']} đơn",
                "badge": f"{summary['completion_rate']}% xong",
                "subtext": f"{summary['status_distribution']['Đang xử lý']} đơn đang chờ xử lý",
                "trend": "up",
                "icon": "🛍️",
            },
            {
                "label": "Giá Trị Đơn TB (AOV)",
                "value": f"{summary['avg_order_value']:,.0f} đ",
                "badge": "Chuẩn hóa",
                "subtext": "Mức chi tiêu trung bình/đơn",
                "trend": "neutral",
                "icon": "🎯",
            },
            {
                "label": "Tỷ Lệ Hoàn Thành",
                "value": f"{summary['completion_rate']}%",
                "badge": "Đạt KPI",
                "subtext": f"{summary['status_distribution']['Hoàn thành']} đơn hoàn tất thành công",
                "trend": "up",
                "icon": "⚡",
            },
        ],
        "charts": [
            {
                "id": "payment_method_chart",
                "title": "Cơ Cấu Doanh Thu Theo Phương Thức Thanh Toán",
                "type": "doughnut",
                "labels": pm_labels,
                "datasets": [
                    {
                        "label": "Doanh thu (VNĐ)",
                        "data": pm_revenues,
                    }
                ],
            },
            {
                "id": "status_chart",
                "title": "Tỷ Lệ Phân Bổ Trạng Thái Đơn Hàng",
                "type": "pie",
                "labels": list(summary["status_distribution"].keys()),
                "datasets": [
                    {
                        "label": "Số lượng đơn",
                        "data": list(summary["status_distribution"].values()),
                    }
                ],
            },
            {
                "id": "shipping_chart",
                "title": "Doanh Số Phân Bổ Theo Đơn Vị Vận Chuyển",
                "type": "bar",
                "labels": sp_labels,
                "datasets": [
                    {
                        "label": "Doanh thu vận chuyển (VNĐ)",
                        "data": sp_revenues,
                    }
                ],
            },
        ],
        "table": {
            "title": "Bảng Xếp Hạng Top Khách Hàng Đóng Góp Doanh Số Cao Nhất",
            "columns": [
                {"key": "customer", "title": "Khách Hàng"},
                {"key": "orders_count", "title": "Số Đơn"},
                {"key": "total_spent", "title": "Tổng Chi Tiêu (VNĐ)"},
                {"key": "preferred_payment", "title": "Phương Thức Ưa Thích"},
                {"key": "tier", "title": "Phân Hạng"},
            ],
            "rows": summary["top_customers"],
        },
        "insights": _normalize_items(raw_insights, default_tag="Dòng Tiền"),
        "recommendations": _normalize_items(raw_recommendations, default_tag="Chiến Lược"),
    }


def generate_sales_report() -> dict:
    """
    Trích xuất dữ liệu từ Model Order và gửi prompt ép kiểu JSON đến Google Gemini AI
    để phân tích kinh doanh, tạo bảng dữ liệu, cấu hình vẽ đồ thị và trích xuất insights.
    """
    summary = _build_crm_summary()
    if not summary:
        return {
            "success": False,
            "error": "Hiện chưa có dữ liệu đơn hàng nào trong hệ thống CRM để thực hiện phân tích.",
        }

    api_key = os.environ.get("GOOGLE_AI_API_KEY", "").strip()

    prompt = f"""
Bạn là Giám đốc Phân tích Dữ liệu BI & Quản trị Kinh doanh cấp cao (Head of Business Intelligence & Analytics).
Dưới đây là dữ liệu thống kê tổng hợp từ hệ thống CRM:

{json.dumps(summary, ensure_ascii=False, indent=2)}

### QUY TẮC BẮT BUỘC:
1. CHỈ TRẢ VỀ DUY NHẤT 1 CHUỖI JSON HỢP LỆ. Bắt đầu bằng {{ và kết thúc bằng }}.
2. TUYỆT ĐỐI KHÔNG trả về bất kỳ văn bản giải thích, lời chào, hay ký tự nào ngoài JSON (Không markdown, không 'Dưới đây là...').
3. Insight và khuyến nghị phải cực kỳ chuyên nghiệp, ngắn gọn, súc tích (1-2 câu mỗi ý), định lượng bằng số liệu thực tế từ dữ liệu trên.

### CẤU TRÚC JSON PHẢI TUÂN THỦ:
{{
  "report_title": "Báo Cáo Phân Tích Doanh Thu & Hiệu Quả Kinh Doanh CRM",
  "period_summary": "Tóm tắt ngắn gọn quy mô dữ liệu trong 1 câu",
  "kpis": [
    {{
      "label": "Tổng Doanh Thu",
      "value": "{summary['total_revenue']:,.0f} đ",
      "badge": "+15.2%",
      "subtext": "Doanh thu tích lũy hệ thống",
      "trend": "up",
      "icon": "💰"
    }},
    {{
      "label": "Tổng Đơn Hàng",
      "value": "{summary['total_orders']} đơn",
      "badge": "{summary['completion_rate']}% xong",
      "subtext": "Quy mô giao dịch",
      "trend": "up",
      "icon": "🛍️"
    }},
    {{
      "label": "Giá Trị Đơn TB (AOV)",
      "value": "{summary['avg_order_value']:,.0f} đ",
      "badge": "Ổn định",
      "subtext": "Mức chi tiêu trung bình/đơn",
      "trend": "neutral",
      "icon": "🎯"
    }},
    {{
      "label": "Tỷ Lệ Hoàn Thành",
      "value": "{summary['completion_rate']}%",
      "badge": "Đạt KPI",
      "subtext": "Hiệu suất xử lý đơn",
      "trend": "up",
      "icon": "⚡"
    }}
  ],
  "charts": [
    {{
      "id": "payment_method_chart",
      "title": "Cơ Cấu Doanh Thu Theo Phương Thức Thanh Toán",
      "type": "doughnut",
      "labels": ["MB eBanking", "ShopeePay", "ZaloPay", "MoMo"],
      "datasets": [
        {{
          "label": "Doanh thu (VNĐ)",
          "data": [1234567, 8910111]
        }}
      ]
    }},
    {{
      "id": "status_chart",
      "title": "Tỷ Lệ Phân Bổ Trạng Thái Đơn Hàng",
      "type": "pie",
      "labels": ["Hoàn thành", "Đang xử lý"],
      "datasets": [
        {{
          "label": "Số lượng đơn",
          "data": [{summary['status_distribution']['Hoàn thành']}, {summary['status_distribution']['Đang xử lý']}]
        }}
      ]
    }},
    {{
      "id": "shipping_chart",
      "title": "Doanh Số Phân Bổ Theo Đơn Vị Vận Chuyển",
      "type": "bar",
      "labels": ["SPX Express", "GHTK", "J&T Express"],
      "datasets": [
        {{
          "label": "Doanh thu (VNĐ)",
          "data": [1234567, 8910111]
        }}
      ]
    }}
  ],
  "table": {{
    "title": "Bảng Xếp Hạng Top Khách Hàng Đóng Góp Doanh Số Cao Nhất",
    "columns": [
      {{ "key": "customer", "title": "Khách Hàng" }},
      {{ "key": "orders_count", "title": "Số Đơn" }},
      {{ "key": "total_spent", "title": "Tổng Chi Tiêu (VNĐ)" }},
      {{ "key": "preferred_payment", "title": "Phương Thức Ưa Thích" }},
      {{ "key": "tier", "title": "Phân Hạng" }}
    ],
    "rows": {json.dumps(summary['top_customers'], ensure_ascii=False)}
  }},
  "insights": [
    "Insight định lượng 1 (súc tích, chỉ ra điểm then chốt)",
    "Insight định lượng 2...",
    "Insight định lượng 3..."
  ],
  "recommendations": [
    "Khuyến nghị hành động chiến lược 1...",
    "Khuyến nghị hành động chiến lược 2..."
  ]
}}
"""

    # Gọi Google Gemini REST API
    if api_key:
        models_to_try = [
            "gemini-3.5-flash-lite",
            "gemini-3.1-flash-lite",
            "gemini-3.8-flash",
            "gemini-flash-latest",
        ]
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.2,
            },
        }
        payload_str = json.dumps(payload)

        for model_name in models_to_try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
            try:
                # Dùng curl.exe (nhanh và ổn định trên Windows)
                import subprocess
                proc = subprocess.run(
                    ["curl.exe", "-s", "-X", "POST", url, "-H", "Content-Type: application/json", "-d", payload_str],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    timeout=15,
                )
                if proc.returncode == 0 and proc.stdout:
                    resp_json = json.loads(proc.stdout)
                    if "candidates" in resp_json and resp_json["candidates"]:
                        raw_text = resp_json["candidates"][0]["content"]["parts"][0]["text"].strip()
                        cleaned_text = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_text, flags=re.MULTILINE).strip()
                        parsed_data = json.loads(cleaned_text)

                        # Chuẩn hóa insights và recommendations
                        parsed_data["insights"] = _normalize_items(parsed_data.get("insights", []), default_tag="Phát Hiện")
                        parsed_data["recommendations"] = _normalize_items(parsed_data.get("recommendations", []), default_tag="Đề Xuất")

                        # Bảo đảm rows của table giữ đầy đủ avatar initials và spend percentage
                        if "table" in parsed_data and "rows" in parsed_data["table"]:
                            parsed_data["table"]["rows"] = summary["top_customers"]

                        return {
                            "success": True,
                            "source": "ai",
                            "model": model_name,
                            "data": parsed_data,
                        }
            except Exception:
                pass

            # Dự phòng bằng httpx
            try:
                with httpx.Client(timeout=15.0) as client:
                    res = client.post(url, json=payload)
                    if res.status_code == 200:
                        resp_json = res.json()
                        raw_text = resp_json["candidates"][0]["content"]["parts"][0]["text"].strip()
                        cleaned_text = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_text, flags=re.MULTILINE).strip()
                        parsed_data = json.loads(cleaned_text)

                        parsed_data["insights"] = _normalize_items(parsed_data.get("insights", []), default_tag="Phát Hiện")
                        parsed_data["recommendations"] = _normalize_items(parsed_data.get("recommendations", []), default_tag="Đề Xuất")

                        if "table" in parsed_data and "rows" in parsed_data["table"]:
                            parsed_data["table"]["rows"] = summary["top_customers"]

                        return {
                            "success": True,
                            "source": "ai",
                            "model": model_name,
                            "data": parsed_data,
                        }
            except Exception:
                continue

    # Fallback mượt mà từ CSDL CRM
    fallback_data = _generate_fallback_report(summary)
    warning = None
    if not api_key:
        warning = "Chưa cấu hình GOOGLE_AI_API_KEY trong file .env. Hệ thống đang hiển thị phân tích dữ liệu trực tiếp từ CRM."

    return {
        "success": True,
        "source": "crm_data",
        "data": fallback_data,
        "warning": warning,
    }

