"""
==========================================================================
 🚀 Script Tự Động Tạo Dashboard Apache Superset với 7 Biểu Đồ
==========================================================================
 Sử dụng Superset REST API để:
 1. Kết nối cơ sở dữ liệu SQLite
 2. Tạo 6 Datasets (crm_order, crm_lead, crm_supportticket,
    crm_revenueforecast, crm_customersegment, + 1 virtual dataset SQL)
 3. Tạo 7 Charts (5 phân tích thực trạng + 2 AI)
 4. Tạo 1 Dashboard gom 7 charts với layout đẹp mắt

 Yêu cầu:
   - Apache Superset đang chạy tại http://localhost:8088
   - Tài khoản admin / admin
   - File CSDL: d:/HocTap/BI/WagtailPrj/wagtail_crm/db.sqlite3
==========================================================================
"""
import json
import sys
import time
import requests

# ── Cấu hình ───────────────────────────────────────────────────────────
SUPERSET_URL = "http://localhost:8088"
USERNAME = "admin"
PASSWORD = "admin"
DB_PATH = "/app/db.sqlite3"
DB_NAME = "Wagtail CRM Database"
DASHBOARD_TITLE = "📊 CRM Business Intelligence & AI Analytics Dashboard"

# Bảng màu xanh dương chủ đạo
BLUE_PALETTE = [
    "#1e3a5f", "#2563eb", "#3b82f6", "#60a5fa",
    "#93c5fd", "#bfdbfe", "#0284c7", "#0369a1"
]

session = requests.Session()


# ── Tiện ích ─────────────────────────────────────────────────────────
def log(msg, level="INFO"):
    icons = {"INFO": "ℹ️", "OK": "✅", "WARN": "⚠️", "ERR": "❌", "STEP": "🔹"}
    print(f"  {icons.get(level, '•')} [{level}] {msg}")


def api(method, path, **kwargs):
    """Gọi Superset REST API với CSRF token tự động."""
    url = f"{SUPERSET_URL}{path}"
    headers = kwargs.pop("headers", {})
    headers["Authorization"] = f"Bearer {session.access_token}"
    headers["Referer"] = SUPERSET_URL

    # Lấy CSRF token cho POST/PUT/DELETE
    if method.upper() in ("POST", "PUT", "DELETE"):
        csrf_resp = session.get(
            f"{SUPERSET_URL}/api/v1/security/csrf_token/",
            headers={"Authorization": f"Bearer {session.access_token}"},
        )
        if csrf_resp.ok:
            headers["X-CSRFToken"] = csrf_resp.json()["result"]

    resp = getattr(session, method.lower())(url, headers=headers, **kwargs)
    return resp


# ══════════════════════════════════════════════════════════════════════
# BƯỚC 1: Đăng nhập & lấy Access Token
# ══════════════════════════════════════════════════════════════════════
def login():
    log("Đăng nhập vào Apache Superset...", "STEP")
    resp = session.post(
        f"{SUPERSET_URL}/api/v1/security/login",
        json={"username": USERNAME, "password": PASSWORD, "provider": "db", "refresh": True},
    )
    if resp.status_code != 200:
        log(f"Không thể đăng nhập! Status={resp.status_code} Body={resp.text}", "ERR")
        sys.exit(1)
    session.access_token = resp.json()["access_token"]
    log(f"Đăng nhập thành công ✓ (token: ...{session.access_token[-8:]})", "OK")


# ══════════════════════════════════════════════════════════════════════
# BƯỚC 2: Kết nối Database SQLite
# ══════════════════════════════════════════════════════════════════════
def get_or_create_database():
    log("Kết nối cơ sở dữ liệu SQLite...", "STEP")

    # Kiểm tra đã tồn tại chưa
    resp = api("get", "/api/v1/database/", params={"q": json.dumps({"filters": [{"col": "database_name", "opr": "eq", "value": DB_NAME}]})})
    if resp.ok and resp.json().get("count", 0) > 0:
        db_id = resp.json()["result"][0]["id"]
        log(f"Database đã tồn tại: id={db_id}", "OK")
        return db_id

    # Tạo mới
    payload = {
        "database_name": DB_NAME,
        "sqlalchemy_uri": f"sqlite:///{DB_PATH}",
        "expose_in_sqllab": True,
        "allow_ctas": False,
        "allow_cvas": True,
        "allow_dml": False,
        "allow_run_async": False,
    }
    resp = api("post", "/api/v1/database/", json=payload)
    if resp.status_code in (200, 201):
        db_id = resp.json()["id"]
        log(f"Đã tạo Database: id={db_id}", "OK")
        return db_id
    else:
        log(f"Lỗi tạo Database: {resp.status_code} {resp.text}", "ERR")
        sys.exit(1)


# ══════════════════════════════════════════════════════════════════════
# BƯỚC 3: Tạo Datasets
# ══════════════════════════════════════════════════════════════════════
def get_or_create_dataset(db_id, table_name, schema=None):
    """Tạo hoặc lấy Physical Dataset từ bảng có sẵn."""
    # Tìm dataset đã có
    filters = [
        {"col": "table_name", "opr": "eq", "value": table_name},
        {"col": "database", "opr": "rel_o_m", "value": db_id},
    ]
    resp = api("get", "/api/v1/dataset/", params={"q": json.dumps({"filters": filters})})
    if resp.ok and resp.json().get("count", 0) > 0:
        ds_id = resp.json()["result"][0]["id"]
        log(f"  Dataset '{table_name}' đã tồn tại: id={ds_id}", "OK")
        return ds_id

    payload = {
        "database": db_id,
        "table_name": table_name,
        "schema": schema or "",
    }
    resp = api("post", "/api/v1/dataset/", json=payload)
    if resp.status_code in (200, 201):
        ds_id = resp.json()["id"]
        log(f"  Đã tạo Dataset '{table_name}': id={ds_id}", "OK")
        return ds_id
    else:
        log(f"  Lỗi tạo Dataset '{table_name}': {resp.status_code} {resp.text}", "WARN")
        return None


def create_virtual_dataset(db_id, name, sql):
    """Tạo Virtual Dataset (SQL Lab query)."""
    filters = [
        {"col": "table_name", "opr": "eq", "value": name},
        {"col": "database", "opr": "rel_o_m", "value": db_id},
    ]
    resp = api("get", "/api/v1/dataset/", params={"q": json.dumps({"filters": filters})})
    if resp.ok and resp.json().get("count", 0) > 0:
        ds_id = resp.json()["result"][0]["id"]
        log(f"  Virtual Dataset '{name}' đã tồn tại: id={ds_id}", "OK")
        return ds_id

    payload = {
        "database": db_id,
        "table_name": name,
        "schema": "",
        "sql": sql,
    }
    resp = api("post", "/api/v1/dataset/", json=payload)
    if resp.status_code in (200, 201):
        ds_id = resp.json()["id"]
        log(f"  Đã tạo Virtual Dataset '{name}': id={ds_id}", "OK")
        return ds_id
    else:
        log(f"  Lỗi tạo Virtual Dataset '{name}': {resp.status_code} {resp.text}", "WARN")
        return None


def setup_datasets(db_id):
    log("Tạo Datasets cho 7 biểu đồ...", "STEP")
    datasets = {}

    # Physical datasets
    for table in ["crm_order", "crm_lead", "crm_supportticket", "crm_revenueforecast", "crm_customersegment"]:
        ds_id = get_or_create_dataset(db_id, table)
        if ds_id:
            datasets[table] = ds_id

    # Virtual dataset cho biểu đồ 4 (Product Revenue)
    product_sql = """
SELECT
    p.category AS product_category,
    p.name AS product_name,
    SUM(oi.quantity) AS total_quantity_sold,
    ROUND(SUM(oi.quantity * oi.unit_price), 0) AS total_revenue
FROM crm_orderitem oi
JOIN crm_product p ON oi.product_id = p.id
JOIN crm_order o ON oi.order_id = o.id
WHERE o.status = 'completed'
GROUP BY p.category, p.name
ORDER BY total_revenue DESC
"""
    ds_id = create_virtual_dataset(db_id, "vw_product_revenue", product_sql)
    if ds_id:
        datasets["vw_product_revenue"] = ds_id

    return datasets


# ══════════════════════════════════════════════════════════════════════
# BƯỚC 4: Tạo 7 Charts
# ══════════════════════════════════════════════════════════════════════

def create_chart(name, viz_type, datasource_id, params_dict):
    """Tạo 1 chart trên Superset."""
    # Kiểm tra đã có chưa
    filters = [{"col": "slice_name", "opr": "eq", "value": name}]
    resp = api("get", "/api/v1/chart/", params={"q": json.dumps({"filters": filters})})
    if resp.ok and resp.json().get("count", 0) > 0:
        chart_id = resp.json()["result"][0]["id"]
        log(f"    Chart '{name}' đã tồn tại: id={chart_id}", "OK")
        return chart_id

    payload = {
        "slice_name": name,
        "viz_type": viz_type,
        "datasource_id": datasource_id,
        "datasource_type": "table",
        "params": json.dumps(params_dict),
    }
    resp = api("post", "/api/v1/chart/", json=payload)
    if resp.status_code in (200, 201):
        chart_id = resp.json()["id"]
        log(f"    Chart '{name}' đã tạo thành công: id={chart_id}", "OK")
        return chart_id
    else:
        log(f"    Lỗi tạo Chart '{name}': {resp.status_code} {resp.text}", "WARN")
        return None


def create_all_charts(datasets):
    log("Tạo 7 biểu đồ phân tích...", "STEP")
    chart_ids = []

    # ─────────────────────────────────────────────────────────────
    # CHART 1: Xu hướng Doanh thu & Đơn hàng theo Thời gian
    # ─────────────────────────────────────────────────────────────
    log("  📊 [1/7] Xu hướng Doanh thu & Đơn hàng theo Thời gian", "STEP")
    c1 = create_chart(
        name="📈 Xu Hướng Doanh Thu & Số Đơn Hàng Theo Thời Gian",
        viz_type="mixed_timeseries",
        datasource_id=datasets["crm_order"],
        params_dict={
            "x_axis": "created_at",
            "time_grain_sqla": "P1W",
            "metrics": [{"label": "Doanh Thu (VNĐ)", "expressionType": "SQL", "sqlExpression": "SUM(CASE WHEN status='completed' THEN total_amount ELSE 0 END)"}],
            "metrics_b": [{"label": "Số Đơn Hàng", "expressionType": "SQL", "sqlExpression": "COUNT(id)"}],
            "adhoc_filters": [],
            "truncateYAxis": False,
            "y_axis_format": ",.0f",
            "y_axis_2_format": ",.0f",
            "color_scheme": "supersetColors",
            "show_legend": True,
            "legendType": "scroll",
            "legendOrientation": "top",
            "rich_tooltip": True,
            "tooltipTimeFormat": "%d/%m/%Y",
            "x_axis_title": "Thời gian",
            "y_axis_title": "Doanh thu (VNĐ)",
            "y_axis_title_secondary": "Số đơn",
            "zoomable": True,
            "row_limit": 10000,
            "header_font_size": 0.4,
        },
    )
    if c1:
        chart_ids.append(c1)

    # ─────────────────────────────────────────────────────────────
    # CHART 2: Phễu Chuyển đổi Sales Pipeline (Leads Funnel)
    # ─────────────────────────────────────────────────────────────
    log("  📊 [2/7] Phễu Chuyển Đổi Cơ Hội Sales Pipeline", "STEP")
    c2 = create_chart(
        name="🎯 Phễu Chuyển Đổi Cơ Hội Sales Pipeline",
        viz_type="funnel",
        datasource_id=datasets["crm_lead"],
        params_dict={
            "groupby": ["status"],
            "metric": {"label": "Số cơ hội", "expressionType": "SQL", "sqlExpression": "COUNT(id)"},
            "row_limit": 50,
            "color_scheme": "supersetColors",
            "show_legend": True,
            "show_labels": True,
            "label_type": "key_value_percent",
            "number_format": ",.0f",
            "header_font_size": 0.4,
        },
    )
    if c2:
        chart_ids.append(c2)

    # ─────────────────────────────────────────────────────────────
    # CHART 3: Cơ cấu Thanh toán & Vận chuyển (Sunburst / Pie)
    # ─────────────────────────────────────────────────────────────
    log("  📊 [3/7] Cơ Cấu Doanh Thu Theo Thanh Toán & Vận Chuyển", "STEP")
    c3 = create_chart(
        name="💳 Cơ Cấu Doanh Thu Theo Thanh Toán & Vận Chuyển",
        viz_type="sunburst_v2",
        datasource_id=datasets["crm_order"],
        params_dict={
            "columns": ["payment_method", "shipping_provider"],
            "metric": {"label": "Doanh Thu", "expressionType": "SQL", "sqlExpression": "SUM(total_amount)"},
            "color_scheme": "supersetColors",
            "show_labels": True,
            "show_labels_threshold": 5,
            "number_format": ",.0f",
            "header_font_size": 0.4,
            "adhoc_filters": [
                {
                    "expressionType": "SQL",
                    "sqlExpression": "status = 'completed'",
                    "clause": "WHERE",
                }
            ],
        },
    )
    if c3:
        chart_ids.append(c3)

    # ─────────────────────────────────────────────────────────────
    # CHART 4: Top Sản phẩm & Danh mục (Treemap)
    # ─────────────────────────────────────────────────────────────
    log("  📊 [4/7] Top Sản Phẩm & Danh Mục Doanh Thu Cao Nhất", "STEP")
    if "vw_product_revenue" in datasets:
        c4 = create_chart(
            name="🏆 Top Sản Phẩm & Danh Mục Doanh Thu Cao Nhất",
            viz_type="treemap_v2",
            datasource_id=datasets["vw_product_revenue"],
            params_dict={
                "groupby": ["product_category", "product_name"],
                "metric": {"label": "Doanh Thu", "expressionType": "SIMPLE", "column": {"column_name": "total_revenue"}, "aggregate": "SUM"},
                "color_scheme": "supersetColors",
                "show_labels": True,
                "show_upper_labels": True,
                "number_format": ",.0f",
                "header_font_size": 0.4,
                "treemap_ratio": 1.618,
            },
        )
        if c4:
            chart_ids.append(c4)

    # ─────────────────────────────────────────────────────────────
    # CHART 5: Chất lượng Hỗ trợ & Ticket (Stacked Bar)
    # ─────────────────────────────────────────────────────────────
    log("  📊 [5/7] Phân Bổ Ticket Hỗ Trợ Theo Mức Độ Ưu Tiên", "STEP")
    c5 = create_chart(
        name="🛡️ Phân Bổ Ticket Hỗ Trợ Theo Mức Độ Ưu Tiên & Trạng Thái",
        viz_type="echarts_timeseries_bar",
        datasource_id=datasets["crm_supportticket"],
        params_dict={
            "x_axis": "priority",
            "metrics": [{"label": "Số Ticket", "expressionType": "SQL", "sqlExpression": "COUNT(id)"}],
            "groupby": ["status"],
            "show_legend": True,
            "legendOrientation": "top",
            "legendType": "scroll",
            "stack": "Stack",
            "show_value": True,
            "color_scheme": "supersetColors",
            "y_axis_format": ",.0f",
            "x_axis_title": "Mức độ ưu tiên",
            "y_axis_title": "Số lượng Ticket",
            "rich_tooltip": True,
            "row_limit": 10000,
            "header_font_size": 0.4,
        },
    )
    if c5:
        chart_ids.append(c5)

    # ─────────────────────────────────────────────────────────────
    # CHART 6 (AI): Dự báo Doanh thu 30 ngày (Line + Confidence)
    # ─────────────────────────────────────────────────────────────
    log("  📊 [6/7] 🤖 Dự Báo Doanh Thu 30 Ngày (Ridge Regression + CI 95%)", "STEP")
    c6 = create_chart(
        name="🤖 Dự Báo Doanh Thu 30 Ngày Tới (AI Ridge Regression)",
        viz_type="echarts_area",
        datasource_id=datasets["crm_revenueforecast"],
        params_dict={
            "x_axis": "forecast_date",
            "time_grain_sqla": "P1D",
            "metrics": [
                {"label": "Doanh Thu Dự Báo", "expressionType": "SIMPLE", "column": {"column_name": "predicted_revenue"}, "aggregate": "AVG"},
                {"label": "Cận Trên (CI 95%)", "expressionType": "SIMPLE", "column": {"column_name": "upper_bound"}, "aggregate": "AVG"},
                {"label": "Cận Dưới (CI 95%)", "expressionType": "SIMPLE", "column": {"column_name": "lower_bound"}, "aggregate": "AVG"},
            ],
            "color_scheme": "supersetColors",
            "show_legend": True,
            "legendOrientation": "top",
            "legendType": "scroll",
            "rich_tooltip": True,
            "tooltipTimeFormat": "%d/%m/%Y",
            "y_axis_format": ",.0f",
            "x_axis_title": "Ngày dự báo",
            "y_axis_title": "Doanh thu dự báo (VNĐ)",
            "opacity": 0.2,
            "markerEnabled": True,
            "markerSize": 6,
            "zoomable": True,
            "row_limit": 10000,
            "header_font_size": 0.4,
        },
    )
    if c6:
        chart_ids.append(c6)

    # ─────────────────────────────────────────────────────────────
    # CHART 7 (AI): Phân khúc KH RFM & Churn Risk (Scatter / Bubble)
    # ─────────────────────────────────────────────────────────────
    log("  📊 [7/7] 🤖 Phân Khúc Khách Hàng RFM & Nguy Cơ Rời Bỏ", "STEP")
    c7 = create_chart(
        name="🤖 Phân Khúc Khách Hàng RFM & Nguy Cơ Rời Bỏ (K-Means AI)",
        viz_type="bubble_v2",
        datasource_id=datasets["crm_customersegment"],
        params_dict={
            "x_axis": {"label": "Recency (Ngày chưa mua)", "expressionType": "SIMPLE", "column": {"column_name": "recency_days"}, "aggregate": "AVG"},
            "y_axis": {"label": "Monetary (Tổng chi tiêu)", "expressionType": "SIMPLE", "column": {"column_name": "monetary"}, "aggregate": "AVG"},
            "size": {"label": "Frequency (Số đơn)", "expressionType": "SIMPLE", "column": {"column_name": "frequency"}, "aggregate": "AVG"},
            "entity": "segment_label",
            "series": "churn_risk",
            "color_scheme": "supersetColors",
            "show_legend": True,
            "max_bubble_size": "50",
            "y_axis_format": ",.0f",
            "x_axis_label": "Recency (Số ngày chưa mua hàng)",
            "y_axis_label": "Monetary (Tổng chi tiêu VNĐ)",
            "row_limit": 10000,
            "header_font_size": 0.4,
        },
    )
    if c7:
        chart_ids.append(c7)

    return chart_ids


# ══════════════════════════════════════════════════════════════════════
# BƯỚC 5: Tạo Dashboard với Layout Grid đẹp
# ══════════════════════════════════════════════════════════════════════

def build_dashboard_layout(chart_ids):
    """
    Xây dựng position_json cho dashboard.
    Layout: Header + 2 hàng charts (3+2+2 = 7 charts)
    Mỗi chart cách nhau bởi khoảng trống (border effect).
    Superset grid: 12 cột, mỗi row chiều cao ~ 50-60 units.
    """
    layout = {
        "DASHBOARD_VERSION_KEY": "v2",
        "ROOT_ID": {"type": "ROOT", "id": "ROOT_ID", "children": ["GRID_ID"]},
        "GRID_ID": {"type": "GRID", "id": "GRID_ID", "children": [], "parents": ["ROOT_ID"]},
        "HEADER_ID": {
            "type": "HEADER",
            "id": "HEADER_ID",
            "meta": {"text": DASHBOARD_TITLE},
        },
    }

    grid_children = []

    # Row configs: list of (chart_index_in_chart_ids, width_in_grid_cols)
    # Row 1: Chart 0 (6 cols) + Chart 1 (6 cols)
    # Row 2: Chart 2 (4 cols) + Chart 3 (4 cols) + Chart 4 (4 cols)
    # Row 3 (AI): Chart 5 (6 cols) + Chart 6 (6 cols)
    rows = [
        [(0, 6), (1, 6)],
        [(2, 4), (3, 4), (4, 4)],
        [(5, 6), (6, 6)],
    ]

    row_idx = 0
    for row_config in rows:
        row_id = f"ROW-{row_idx}"
        row_obj = {
            "type": "ROW",
            "id": row_id,
            "children": [],
            "parents": ["ROOT_ID", "GRID_ID"],
            "meta": {"background": "BACKGROUND_TRANSPARENT"},
        }

        for chart_offset, width in row_config:
            if chart_offset >= len(chart_ids):
                continue
            chart_id = chart_ids[chart_offset]
            comp_id = f"CHART-{chart_id}"

            chart_comp = {
                "type": "CHART",
                "id": comp_id,
                "children": [],
                "parents": ["ROOT_ID", "GRID_ID", row_id],
                "meta": {
                    "chartId": chart_id,
                    "width": width,
                    "height": 55,
                    "sliceName": "",
                    "uuid": f"chart-uuid-{chart_id}",
                },
            }
            layout[comp_id] = chart_comp
            row_obj["children"].append(comp_id)

        layout[row_id] = row_obj
        grid_children.append(row_id)
        row_idx += 1

    layout["GRID_ID"]["children"] = grid_children
    return layout


def create_dashboard(chart_ids):
    log("Tạo Dashboard tổng hợp...", "STEP")

    # Kiểm tra đã tồn tại chưa
    filters = [{"col": "dashboard_title", "opr": "eq", "value": DASHBOARD_TITLE}]
    resp = api("get", "/api/v1/dashboard/", params={"q": json.dumps({"filters": filters})})
    if resp.ok and resp.json().get("count", 0) > 0:
        dash_id = resp.json()["result"][0]["id"]
        log(f"Dashboard đã tồn tại: id={dash_id}. Cập nhật lại...", "WARN")
        # Cập nhật dashboard hiện tại
        position = build_dashboard_layout(chart_ids)
        css = get_dashboard_css()
        payload = {
            "dashboard_title": DASHBOARD_TITLE,
            "position_json": json.dumps(position),
            "css": css,
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
        resp = api("put", f"/api/v1/dashboard/{dash_id}", json=payload)
        if resp.ok:
            log(f"Đã cập nhật Dashboard: id={dash_id}", "OK")
        else:
            log(f"Lỗi cập nhật Dashboard: {resp.status_code} {resp.text}", "WARN")
        return dash_id

    # Tạo mới
    position = build_dashboard_layout(chart_ids)
    css = get_dashboard_css()
    payload = {
        "dashboard_title": DASHBOARD_TITLE,
        "position_json": json.dumps(position),
        "css": css,
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
    resp = api("post", "/api/v1/dashboard/", json=payload)
    if resp.status_code in (200, 201):
        dash_id = resp.json()["id"]
        log(f"Đã tạo Dashboard: id={dash_id}", "OK")
        return dash_id
    else:
        log(f"Lỗi tạo Dashboard: {resp.status_code} {resp.text}", "ERR")
        return None


def get_dashboard_css():
    """CSS tùy chỉnh cho Dashboard: phông chữ to, xanh dương + trắng, border rõ ràng."""
    return """
/* ═══════════════════════════════════════════════════════
   CRM BI Dashboard — Custom Theme: Blue & White
   ═══════════════════════════════════════════════════════ */

/* === Nền Dashboard === */
.dashboard-content,
.grid-container,
.dashboard {
    background-color: #f0f4f8 !important;
}

/* === Header Dashboard === */
.header-title .editable-title input,
.header-title .editable-title span {
    font-size: 28px !important;
    font-weight: 800 !important;
    color: #1e3a5f !important;
    letter-spacing: -0.5px;
    font-family: 'Inter', 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

/* === Chart Container: Border + Shadow + Rounded === */
.dashboard-component-chart-holder {
    background: #ffffff !important;
    border: 1.5px solid #bfdbfe !important;
    border-radius: 14px !important;
    box-shadow: 0 2px 12px rgba(30, 58, 95, 0.07) !important;
    margin: 8px !important;
    padding: 6px !important;
    transition: box-shadow 0.2s ease, border-color 0.2s ease;
}

.dashboard-component-chart-holder:hover {
    border-color: #3b82f6 !important;
    box-shadow: 0 4px 20px rgba(37, 99, 235, 0.12) !important;
}

/* === Chart Header / Title: phông to, đậm, xanh === */
.chart-header .header-title span,
.slice_container .header-title span,
.chart-header span.header-title,
.editable-title span {
    font-size: 16px !important;
    font-weight: 700 !important;
    color: #1e3a5f !important;
    font-family: 'Inter', 'Plus Jakarta Sans', -apple-system, sans-serif !important;
}

/* === Khoảng cách giữa các row === */
.grid-row {
    margin-bottom: 12px !important;
}

/* === Tabs (nếu có) === */
.dashboard-component-tabs .ant-tabs-tab {
    font-size: 14px !important;
    font-weight: 600 !important;
    color: #334155 !important;
}

.dashboard-component-tabs .ant-tabs-tab-active {
    color: #2563eb !important;
}

.dashboard-component-tabs .ant-tabs-ink-bar {
    background-color: #2563eb !important;
}

/* === Scrollbar nhỏ gọn === */
.grid-container::-webkit-scrollbar {
    width: 6px;
}

.grid-container::-webkit-scrollbar-thumb {
    background: #93c5fd;
    border-radius: 3px;
}

/* === Filter Bar === */
.filter-bar {
    background: #ffffff !important;
    border-right: 1px solid #e2e8f0 !important;
}

/* === Nút bấm, badge === */
.ant-btn-primary,
.superset-button.cta {
    background-color: #2563eb !important;
    border-color: #2563eb !important;
}

/* === Tooltip === */
.recharts-tooltip-wrapper .recharts-default-tooltip {
    background: #1e3a5f !important;
    border: none !important;
    border-radius: 8px !important;
    color: #ffffff !important;
    font-size: 13px !important;
}
"""


# ══════════════════════════════════════════════════════════════════════
# MAIN: Chạy toàn bộ pipeline
# ══════════════════════════════════════════════════════════════════════
def main():
    print()
    print("=" * 72)
    print("  🚀 TẠO DASHBOARD APACHE SUPERSET TỰ ĐỘNG")
    print("     7 Biểu đồ BI + AI Analytics | Theme Blue & White")
    print("=" * 72)
    print()

    # 1. Đăng nhập
    login()

    # 2. Kết nối Database
    db_id = get_or_create_database()

    # 3. Tạo Datasets
    datasets = setup_datasets(db_id)
    if len(datasets) < 5:
        log(f"Chỉ tạo được {len(datasets)}/6 datasets. Vẫn tiếp tục tạo charts...", "WARN")

    # 4. Tạo 7 Charts
    chart_ids = create_all_charts(datasets)
    log(f"Tổng cộng: {len(chart_ids)}/7 charts đã tạo thành công.", "OK")

    # 5. Tạo Dashboard
    if chart_ids:
        dash_id = create_dashboard(chart_ids)
        if dash_id:
            dash_url = f"{SUPERSET_URL}/superset/dashboard/{dash_id}/"
            print()
            print("=" * 72)
            print(f"  ✅ DASHBOARD ĐÃ TẠO THÀNH CÔNG!")
            print(f"  🔗 Truy cập: {dash_url}")
            print(f"  📊 Số biểu đồ: {len(chart_ids)}")
            print(f"  🎨 Theme: Blue & White | Font size lớn | Border rõ ràng")
            print("=" * 72)
            print()
    else:
        log("Không có chart nào được tạo. Dashboard bị bỏ qua.", "ERR")


if __name__ == "__main__":
    main()
