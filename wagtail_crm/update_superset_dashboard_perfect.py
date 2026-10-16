"""
==========================================================================
 🚀 Script Hoàn Thiện Dashboard Apache Superset: 7 Biểu Đồ Chuẩn Form Data
==========================================================================
- Theme: Xanh dương & Trắng (Blue & White)
- Phông chữ to, rõ ràng
- Viền (Border) đẹp mắt, ngăn cách rõ rệt giữa các biểu đồ
- Cấu trúc chuẩn 100% form_data và query_context của Superset
- 5 Biểu đồ phân tích thực trạng kinh doanh:
    1. Xu Hướng Doanh Thu & Số Đơn Hàng Theo Thời Gian (Line Timeseries)
    2. Phễu Chuyển Đổi Khách Hàng Tiềm Năng (Sales Funnel)
    3. Cơ Cấu Doanh Thu Theo Phương Thức Thanh Toán & Vận Chuyển (Sunburst)
    4. Top Sản Phẩm & Danh Mục Doanh Thu Cao Nhất (Treemap)
    5. Phân Bổ Phiếu Hỗ Trợ Khách Hàng Theo Mức Độ & Trạng Thái (Stacked Bar)
- 2 Biểu đồ kết quả Mô Hình AI:
    6. [AI] Dự Báo Doanh Thu 30 Ngày Tới (Ridge Regression + Confidence Interval) (Area)
    7. [AI] Phân Khúc Khách Hàng RFM & Đánh Giá Nguy Cơ Rời Bỏ (K-Means Clustering) (Bubble)
==========================================================================
"""
import json
import sys
import requests

sys.stdout.reconfigure(encoding='utf-8')

SUPERSET_URL = "http://localhost:8088"
USERNAME = "admin"
PASSWORD = "admin"
DASH_ID = 11

session = requests.Session()

# 1. Đăng nhập & CSRF
def login():
    r = session.post(f"{SUPERSET_URL}/api/v1/security/login", json={
        "username": USERNAME, "password": PASSWORD, "provider": "db", "refresh": True
    })
    token = r.json()["access_token"]
    session.headers.update({"Authorization": f"Bearer {token}"})
    
    csrf = session.get(f"{SUPERSET_URL}/api/v1/security/csrf_token/").json()["result"]
    session.headers.update({"X-CSRFToken": csrf, "Referer": SUPERSET_URL})
    print("✅ Đăng nhập Superset thành công.")

login()

# 2. Định nghĩa chi tiết 7 biểu đồ với cấu hình params và query_context chuẩn
CHARTS_CONFIG = [
    {
        "id": 125,
        "name": "📈 Xu Hướng Doanh Thu & Số Đơn Hàng Theo Thời Gian",
        "viz_type": "echarts_timeseries_line",
        "datasource_id": 23,
        "params": {
            "datasource": "23__table",
            "viz_type": "echarts_timeseries_line",
            "slice_id": 125,
            "x_axis": "created_at",
            "time_grain_sqla": "P1W",
            "metrics": [
                {
                    "expressionType": "SQL",
                    "sqlExpression": "SUM(total_amount)",
                    "label": "Doanh Thu (VNĐ)"
                },
                {
                    "expressionType": "SQL",
                    "sqlExpression": "COUNT(id)",
                    "label": "Số Đơn Hàng"
                }
            ],
            "time_range": "No filter",
            "color_scheme": "supersetColors",
            "show_legend": True,
            "legendOrientation": "top",
            "legendType": "scroll",
            "rich_tooltip": True,
            "tooltipTimeFormat": "%d/%m/%Y",
            "x_axis_title": "Thời gian (Tuần)",
            "y_axis_title": "Doanh thu (VNĐ) / Số lượng đơn",
            "y_axis_format": ",.0f",
            "truncateYAxis": False,
            "zoomable": True,
            "line_interpolation": "smooth",
            "row_limit": 1000
        },
        "query_context": {
            "datasource": {"id": 23, "type": "table"},
            "queries": [{
                "columns": ["created_at"],
                "metrics": [
                    {"expressionType": "SQL", "sqlExpression": "SUM(total_amount)", "label": "Doanh Thu (VNĐ)"},
                    {"expressionType": "SQL", "sqlExpression": "COUNT(id)", "label": "Số Đơn Hàng"}
                ],
                "time_grain_sqla": "P1W",
                "row_limit": 1000
            }],
            "result_format": "json",
            "result_type": "full"
        }
    },
    {
        "id": 126,
        "name": "🎯 Phễu Chuyển Đổi Khách Hàng Tiềm Năng (Sales Pipeline)",
        "viz_type": "funnel",
        "datasource_id": 24,
        "params": {
            "datasource": "24__table",
            "viz_type": "funnel",
            "slice_id": 126,
            "groupby": ["status"],
            "metric": {
                "expressionType": "SQL",
                "sqlExpression": "COUNT(id)",
                "label": "Số Cơ Hội"
            },
            "percent_calculation_type": "first_step",
            "show_labels": True,
            "show_legend": True,
            "legendOrientation": "top",
            "color_scheme": "supersetColors",
            "number_format": ",.0f",
            "sort_by_metric": True,
            "row_limit": 50,
            "time_range": "No filter"
        },
        "query_context": {
            "datasource": {"id": 24, "type": "table"},
            "queries": [{
                "columns": ["status"],
                "groupby": ["status"],
                "metrics": [{"expressionType": "SQL", "sqlExpression": "COUNT(id)", "label": "Số Cơ Hội"}],
                "row_limit": 50
            }],
            "result_format": "json",
            "result_type": "full"
        }
    },
    {
        "id": 127,
        "name": "💳 Cơ Cấu Doanh Thu Theo Thanh Toán & Vận Chuyển",
        "viz_type": "sunburst_v2",
        "datasource_id": 23,
        "params": {
            "datasource": "23__table",
            "viz_type": "sunburst_v2",
            "slice_id": 127,
            "columns": ["payment_method", "shipping_provider"],
            "metric": {
                "expressionType": "SQL",
                "sqlExpression": "SUM(total_amount)",
                "label": "Doanh Thu"
            },
            "color_scheme": "supersetColors",
            "show_labels": True,
            "number_format": ",.0f",
            "row_limit": 100,
            "time_range": "No filter"
        },
        "query_context": {
            "datasource": {"id": 23, "type": "table"},
            "queries": [{
                "columns": ["payment_method", "shipping_provider"],
                "groupby": ["payment_method", "shipping_provider"],
                "metrics": [{"expressionType": "SQL", "sqlExpression": "SUM(total_amount)", "label": "Doanh Thu"}],
                "row_limit": 100
            }],
            "result_format": "json",
            "result_type": "full"
        }
    },
    {
        "id": 128,
        "name": "🏆 Top Sản Phẩm & Danh Mục Doanh Thu Cao Nhất",
        "viz_type": "treemap_v2",
        "datasource_id": 28,
        "params": {
            "datasource": "28__table",
            "viz_type": "treemap_v2",
            "slice_id": 128,
            "groupby": ["product_category", "product_name"],
            "metric": {
                "expressionType": "SIMPLE",
                "column": {"column_name": "total_revenue"},
                "aggregate": "SUM",
                "label": "Doanh Thu"
            },
            "color_scheme": "supersetColors",
            "number_format": ",.0f",
            "treemap_ratio": 1.618,
            "row_limit": 100,
            "time_range": "No filter"
        },
        "query_context": {
            "datasource": {"id": 28, "type": "table"},
            "queries": [{
                "columns": ["product_category", "product_name"],
                "groupby": ["product_category", "product_name"],
                "metrics": [{"expressionType": "SIMPLE", "column": {"column_name": "total_revenue"}, "aggregate": "SUM", "label": "Doanh Thu"}],
                "row_limit": 100
            }],
            "result_format": "json",
            "result_type": "full"
        }
    },
    {
        "id": 129,
        "name": "🛡️ Phân Bổ Phiếu Hỗ Trợ CSKH Theo Ưu Tiên & Trạng Thái",
        "viz_type": "echarts_timeseries_bar",
        "datasource_id": 25,
        "params": {
            "datasource": "25__table",
            "viz_type": "echarts_timeseries_bar",
            "slice_id": 129,
            "x_axis": "priority",
            "groupby": ["status"],
            "metrics": [
                {
                    "expressionType": "SQL",
                    "sqlExpression": "COUNT(id)",
                    "label": "Số Ticket"
                }
            ],
            "stack": "Stack",
            "orientation": "vertical",
            "show_legend": True,
            "legendOrientation": "top",
            "show_value": True,
            "color_scheme": "supersetColors",
            "x_axis_title": "Mức độ ưu tiên",
            "y_axis_title": "Số lượng phiếu hỗ trợ",
            "y_axis_format": ",.0f",
            "row_limit": 100,
            "time_range": "No filter"
        },
        "query_context": {
            "datasource": {"id": 25, "type": "table"},
            "queries": [{
                "columns": ["priority", "status"],
                "groupby": ["priority", "status"],
                "metrics": [{"expressionType": "SQL", "sqlExpression": "COUNT(id)", "label": "Số Ticket"}],
                "row_limit": 100
            }],
            "result_format": "json",
            "result_type": "full"
        }
    },
    {
        "id": 130,
        "name": "🤖 [AI] Dự Báo Doanh Thu 30 Ngày Tới (Ridge Regression + KTC 95%)",
        "viz_type": "echarts_area",
        "datasource_id": 26,
        "params": {
            "datasource": "26__table",
            "viz_type": "echarts_area",
            "slice_id": 130,
            "x_axis": "forecast_date",
            "time_grain_sqla": "P1D",
            "metrics": [
                {
                    "expressionType": "SIMPLE",
                    "column": {"column_name": "predicted_revenue"},
                    "aggregate": "AVG",
                    "label": "Dự Báo Doanh Thu"
                },
                {
                    "expressionType": "SIMPLE",
                    "column": {"column_name": "upper_bound"},
                    "aggregate": "AVG",
                    "label": "Cận Trên (KTC 95%)"
                },
                {
                    "expressionType": "SIMPLE",
                    "column": {"column_name": "lower_bound"},
                    "aggregate": "AVG",
                    "label": "Cận Dưới (KTC 95%)"
                }
            ],
            "color_scheme": "supersetColors",
            "show_legend": True,
            "legendOrientation": "top",
            "rich_tooltip": True,
            "tooltipTimeFormat": "%d/%m/%Y",
            "opacity": 0.25,
            "x_axis_title": "Ngày dự báo",
            "y_axis_title": "Doanh thu dự báo (VNĐ)",
            "y_axis_format": ",.0f",
            "zoomable": True,
            "row_limit": 100,
            "time_range": "No filter"
        },
        "query_context": {
            "datasource": {"id": 26, "type": "table"},
            "queries": [{
                "columns": ["forecast_date"],
                "metrics": [
                    {"expressionType": "SIMPLE", "column": {"column_name": "predicted_revenue"}, "aggregate": "AVG", "label": "Dự Báo Doanh Thu"},
                    {"expressionType": "SIMPLE", "column": {"column_name": "upper_bound"}, "aggregate": "AVG", "label": "Cận Trên (KTC 95%)"},
                    {"expressionType": "SIMPLE", "column": {"column_name": "lower_bound"}, "aggregate": "AVG", "label": "Cận Dưới (KTC 95%)"}
                ],
                "time_grain_sqla": "P1D",
                "row_limit": 100
            }],
            "result_format": "json",
            "result_type": "full"
        }
    },
    {
        "id": 131,
        "name": "🤖 [AI] Phân Khúc Khách Hàng RFM & Nguy Cơ Rời Bỏ (K-Means Clustering)",
        "viz_type": "bubble_v2",
        "datasource_id": 27,
        "params": {
            "datasource": "27__table",
            "viz_type": "bubble_v2",
            "slice_id": 131,
            "entity": "segment_label",
            "series": "churn_risk",
            "x": {
                "expressionType": "SIMPLE",
                "column": {"column_name": "recency_days"},
                "aggregate": "AVG",
                "label": "Recency (Ngày chưa mua)",
                "optionName": "metric_recency"
            },
            "y": {
                "expressionType": "SIMPLE",
                "column": {"column_name": "monetary"},
                "aggregate": "AVG",
                "label": "Monetary (Tổng chi tiêu VNĐ)",
                "optionName": "metric_monetary"
            },
            "size": {
                "expressionType": "SIMPLE",
                "column": {"column_name": "frequency"},
                "aggregate": "AVG",
                "label": "Frequency (Số đơn mua)",
                "optionName": "metric_frequency"
            },
            "max_bubble_size": "60",
            "opacity": 0.75,
            "color_scheme": "supersetColors",
            "show_legend": True,
            "legendOrientation": "top",
            "y_axis_format": ",.0f",
            "x_axis_label": "Số ngày chưa phát sinh đơn hàng (Recency)",
            "y_axis_label": "Tổng giá trị chi tiêu (Monetary - VNĐ)",
            "row_limit": 100,
            "time_range": "No filter"
        },
        "query_context": {
            "datasource": {"id": 27, "type": "table"},
            "queries": [{
                "columns": ["segment_label", "churn_risk"],
                "groupby": ["segment_label", "churn_risk"],
                "metrics": [
                    {"expressionType": "SIMPLE", "column": {"column_name": "recency_days"}, "aggregate": "AVG", "label": "Recency (Ngày chưa mua)"},
                    {"expressionType": "SIMPLE", "column": {"column_name": "monetary"}, "aggregate": "AVG", "label": "Monetary (Tổng chi tiêu VNĐ)"},
                    {"expressionType": "SIMPLE", "column": {"column_name": "frequency"}, "aggregate": "AVG", "label": "Frequency (Số đơn mua)"}
                ],
                "row_limit": 100
            }],
            "result_format": "json",
            "result_type": "full"
        }
    }
]

# 3. Cập nhật từng biểu đồ
chart_uuids = {}
for cfg in CHARTS_CONFIG:
    cid = cfg["id"]
    payload = {
        "slice_name": cfg["name"],
        "viz_type": cfg["viz_type"],
        "datasource_id": cfg["datasource_id"],
        "datasource_type": "table",
        "dashboards": [DASH_ID],
        "params": json.dumps(cfg["params"]),
        "query_context": json.dumps(cfg["query_context"]),
    }
    resp = session.put(f"{SUPERSET_URL}/api/v1/chart/{cid}", json=payload)
    if resp.ok:
        # Lấy UUID
        rc = session.get(f"{SUPERSET_URL}/api/v1/chart/{cid}").json()["result"]
        chart_uuids[cid] = rc["uuid"]
        print(f"  ✅ Cập nhật Chart {cid}: '{cfg['name']}' (UUID: {rc['uuid']})")
    else:
        print(f"  ❌ Lỗi cập nhật Chart {cid}: {resp.status_code} {resp.text}")

# 4. Tạo Header Markdown giới thiệu Dashboard & phân chia khu vực
HEADER_MARKDOWN = """
<div style="
    background: linear-gradient(135deg, #1e3a5f 0%, #2563eb 100%);
    color: #ffffff;
    padding: 22px 28px;
    border-radius: 12px;
    margin-bottom: 6px;
    box-shadow: 0 4px 16px rgba(30, 58, 95, 0.15);
    display: flex;
    justify-content: space-between;
    align-items: center;
">
    <div>
        <h1 style="margin: 0; font-size: 24px; font-weight: 800; letter-spacing: -0.3px; color: #ffffff;">
            📊 HỆ THỐNG PHÂN TÍCH KINH DOANH CRM & DỰ BÁO TRÍ TUỆ NHÂN TẠO (AI)
        </h1>
        <p style="margin: 6px 0 0 0; font-size: 14px; opacity: 0.92; color: #e0e7ff;">
            Theo dõi sức khỏe doanh nghiệp đa chiều & Khai thác sức mạnh mô hình học máy (Ridge Regression & K-Means RFM)
        </p>
    </div>
    <div style="text-align: right; font-size: 13px; color: #bfdbfe; line-height: 1.6;">
        <span style="background: rgba(255,255,255,0.18); padding: 4px 10px; border-radius: 6px; font-weight: 600;">
            🔵 Superset BI Engine
        </span>
    </div>
</div>
"""

SECTION_BI_MARKDOWN = """
<div style="
    background: #ffffff;
    border-left: 5px solid #2563eb;
    padding: 10px 16px;
    border-radius: 6px;
    margin-top: 4px;
    margin-bottom: 4px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
">
    <h3 style="margin: 0; font-size: 16px; font-weight: 700; color: #1e3a5f;">
        🏢 PHẦN 1: BÁO CÁO THỰC TRẠNG DOANH NGHIỆP (5 BIỂU ĐỒ BI CHUYÊN SÂU)
    </h3>
</div>
"""

SECTION_AI_MARKDOWN = """
<div style="
    background: #ffffff;
    border-left: 5px solid #0284c7;
    padding: 10px 16px;
    border-radius: 6px;
    margin-top: 8px;
    margin-bottom: 4px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
">
    <h3 style="margin: 0; font-size: 16px; font-weight: 700; color: #0284c7;">
        🤖 PHẦN 2: KẾT QUẢ MÔ HÌNH HỌC MÁY & DỰ BÁO AI (2 BIỂU ĐỒ AI)
    </h3>
</div>
"""

# 5. Xây dựng Position JSON với Grid Layout chuyên nghiệp
layout = {
    "DASHBOARD_VERSION_KEY": "v2",
    "ROOT_ID": {"type": "ROOT", "id": "ROOT_ID", "children": ["GRID_ID"]},
    "GRID_ID": {"type": "GRID", "id": "GRID_ID", "children": [], "parents": ["ROOT_ID"]},
}

# Markdown Header Banner
layout["HEADER_BANNER"] = {
    "type": "MARKDOWN",
    "id": "HEADER_BANNER",
    "children": [],
    "parents": ["ROOT_ID", "GRID_ID", "ROW_HDR"],
    "meta": {"code": HEADER_MARKDOWN, "height": 18, "width": 12}
}
layout["ROW_HDR"] = {
    "type": "ROW",
    "id": "ROW_HDR",
    "children": ["HEADER_BANNER"],
    "parents": ["ROOT_ID", "GRID_ID"],
    "meta": {"background": "BACKGROUND_TRANSPARENT"}
}

# BI Section Divider
layout["SEC_BI"] = {
    "type": "MARKDOWN",
    "id": "SEC_BI",
    "children": [],
    "parents": ["ROOT_ID", "GRID_ID", "ROW_SEC_BI"],
    "meta": {"code": SECTION_BI_MARKDOWN, "height": 8, "width": 12}
}
layout["ROW_SEC_BI"] = {
    "type": "ROW",
    "id": "ROW_SEC_BI",
    "children": ["SEC_BI"],
    "parents": ["ROOT_ID", "GRID_ID"],
    "meta": {"background": "BACKGROUND_TRANSPARENT"}
}

# Row 1 (BI): Chart 125 (6 cols) + Chart 126 (6 cols)
def make_chart_comp(cid, row_id, width, height):
    comp_id = f"CHART-crm-{cid}"
    cfg = next(c for c in CHARTS_CONFIG if c["id"] == cid)
    return comp_id, {
        "type": "CHART",
        "id": comp_id,
        "children": [],
        "parents": ["ROOT_ID", "GRID_ID", row_id],
        "meta": {
            "chartId": cid,
            "height": height,
            "width": width,
            "sliceName": cfg["name"],
            "uuid": chart_uuids.get(cid, ""),
        }
    }

c125_id, c125_comp = make_chart_comp(125, "ROW_BI_1", 6, 56)
c126_id, c126_comp = make_chart_comp(126, "ROW_BI_1", 6, 56)
layout[c125_id] = c125_comp
layout[c126_id] = c126_comp
layout["ROW_BI_1"] = {
    "type": "ROW",
    "id": "ROW_BI_1",
    "children": [c125_id, c126_id],
    "parents": ["ROOT_ID", "GRID_ID"],
    "meta": {"background": "BACKGROUND_TRANSPARENT"}
}

# Row 2 (BI): Chart 127 (4 cols) + Chart 128 (4 cols) + Chart 129 (4 cols)
c127_id, c127_comp = make_chart_comp(127, "ROW_BI_2", 4, 52)
c128_id, c128_comp = make_chart_comp(128, "ROW_BI_2", 4, 52)
c129_id, c129_comp = make_chart_comp(129, "ROW_BI_2", 4, 52)
layout[c127_id] = c127_comp
layout[c128_id] = c128_comp
layout[c129_id] = c129_comp
layout["ROW_BI_2"] = {
    "type": "ROW",
    "id": "ROW_BI_2",
    "children": [c127_id, c128_id, c129_id],
    "parents": ["ROOT_ID", "GRID_ID"],
    "meta": {"background": "BACKGROUND_TRANSPARENT"}
}

# AI Section Divider
layout["SEC_AI"] = {
    "type": "MARKDOWN",
    "id": "SEC_AI",
    "children": [],
    "parents": ["ROOT_ID", "GRID_ID", "ROW_SEC_AI"],
    "meta": {"code": SECTION_AI_MARKDOWN, "height": 8, "width": 12}
}
layout["ROW_SEC_AI"] = {
    "type": "ROW",
    "id": "ROW_SEC_AI",
    "children": ["SEC_AI"],
    "parents": ["ROOT_ID", "GRID_ID"],
    "meta": {"background": "BACKGROUND_TRANSPARENT"}
}

# Row 3 (AI): Chart 130 (6 cols) + Chart 131 (6 cols)
c130_id, c130_comp = make_chart_comp(130, "ROW_AI_1", 6, 56)
c131_id, c131_comp = make_chart_comp(131, "ROW_AI_1", 6, 56)
layout[c130_id] = c130_comp
layout[c131_id] = c131_comp
layout["ROW_AI_1"] = {
    "type": "ROW",
    "id": "ROW_AI_1",
    "children": [c130_id, c131_id],
    "parents": ["ROOT_ID", "GRID_ID"],
    "meta": {"background": "BACKGROUND_TRANSPARENT"}
}

# Root Grid Order
layout["GRID_ID"]["children"] = [
    "ROW_HDR",
    "ROW_SEC_BI",
    "ROW_BI_1",
    "ROW_BI_2",
    "ROW_SEC_AI",
    "ROW_AI_1"
]

# 6. CSS nâng cao: Blue & White Palette + Bold font + Sharp borders
DASHBOARD_CSS = """
/* ═════════════════════════════════════════════════════════════════
   CRM BI & AI Analytics — Blue & White Premium Theme
   ═════════════════════════════════════════════════════════════════ */

/* Nền toàn trang: xám sáng thanh lịch */
.dashboard,
.dashboard-content,
.grid-container {
    background-color: #f1f5f9 !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif !important;
}

/* Thẻ bao bọc biểu đồ: Viền xanh nhạt, bóng đổ nhẹ, bo góc, padding tạo khoảng cách */
.dashboard-component-chart-holder {
    background: #ffffff !important;
    border: 2px solid #bfdbfe !important;
    border-radius: 12px !important;
    box-shadow: 0 4px 14px rgba(30, 58, 95, 0.08) !important;
    margin: 8px !important;
    padding: 6px !important;
    transition: all 0.25s ease-in-out !important;
}

.dashboard-component-chart-holder:hover {
    border-color: #2563eb !important;
    box-shadow: 0 8px 24px rgba(37, 99, 235, 0.16) !important;
    transform: translateY(-2px);
}

/* Tiêu đề biểu đồ: Phông to 17px, đậm, màu xanh đậm quyền lực */
.chart-header .header-title span,
.chart-header span.header-title,
.slice_container .header-title span {
    font-size: 17px !important;
    font-weight: 800 !important;
    color: #1e3a5f !important;
    letter-spacing: -0.2px !important;
}

/* Khoảng cách giữa các hàng để biểu đồ không dính sát vào nhau */
.grid-row {
    margin-bottom: 14px !important;
}

/* Filter bar & Side bar */
.filter-bar {
    background: #ffffff !important;
    border-right: 2px solid #e2e8f0 !important;
}

/* Scrollbar tinh tế */
.grid-container::-webkit-scrollbar {
    width: 7px;
    height: 7px;
}
.grid-container::-webkit-scrollbar-thumb {
    background: #93c5fd;
    border-radius: 4px;
}

/* Markdown cards */
.dashboard-markdown {
    border-radius: 10px !important;
}
"""

# 7. Cập nhật Dashboard
dash_payload = {
    "dashboard_title": "📊 CRM Business Intelligence & AI Analytics Dashboard",
    "position_json": json.dumps(layout),
    "css": DASHBOARD_CSS,
    "published": True,
    "json_metadata": json.dumps({
        "color_scheme": "supersetColors",
        "label_colors": {},
        "refresh_frequency": 0,
        "timed_refresh_immune_slices": [],
        "expanded_slices": {},
        "default_filters": "{}",
        "chart_configuration": {},
    }),
}

resp = session.put(f"{SUPERSET_URL}/api/v1/dashboard/{DASH_ID}", json=dash_payload)
if resp.ok:
    print(f"\n🎉 THÀNH CÔNG! Dashboard ID={DASH_ID} đã được cập nhật hoàn chỉnh!")
    print(f"🔗 Xem dashboard tại: {SUPERSET_URL}/superset/dashboard/{DASH_ID}/")
else:
    print(f"❌ Lỗi cập nhật Dashboard: {resp.status_code} {resp.text}")
