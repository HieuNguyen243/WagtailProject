# crm/views.py
import json
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .services import generate_sales_report


@login_required
def ai_sales_report_view(request):
    """
    View xử lý hiển thị giao diện Báo cáo AI chuyên nghiệp:
    Sử dụng dữ liệu JSON từ AI/CRM để vẽ biểu đồ tương tác, kết xuất bảng dữ liệu và hiển thị insights.
    """
    report_data = None
    report_json = "{}"
    error_message = None
    warning_message = None
    source = None

    if request.method == "POST":
        result = generate_sales_report()
        if result.get("success"):
            report_data = result.get("data")
            report_json = json.dumps(report_data, ensure_ascii=False)
            warning_message = result.get("warning")
            source = result.get("source")
        else:
            error_message = result.get("error", "Đã xảy ra lỗi khi tạo báo cáo.")

    context = {
        "report_data": report_data,
        "report_json": report_json,
        "error_message": error_message,
        "warning_message": warning_message,
        "source": source,
        "page_title": "Báo cáo Phân tích AI & Quản trị Kinh doanh CRM",
    }
    return render(request, "crm/ai_report.html", context)
