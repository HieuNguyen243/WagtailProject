# Executive Revenue Intelligence - Streamlit Minimalist Dashboard

Ứng dụng Streamlit được thiết kế theo tư duy **Ultra-Minimalist (Tối giản tuyệt đối, Zero-Icon)**. Giao diện tập trung vào tỉ lệ kiểu chữ (Typography), khoảng trắng (Whitespace), cấu trúc viền mảnh (Hairline borders) và bảng màu chuẩn mực doanh nghiệp, loại bỏ hoàn toàn các emoji/icon trang trí thừa.

---

## Bảng màu & Quy chuẩn Thiết kế (Design Tokens)

* **Background (`#F8FAFC`):** Tone xám Slate 50 nhẹ nhàng, tránh gây mỏi mắt so với màu trắng tinh (`#FFFFFF`).
* **Surface (`#FFFFFF`):** Khối thẻ nội dung trắng thuần có đường viền 1px (`#E2E8F0`).
* **Primary Text (`#0F172A`):** Tone xám đen chì tạo độ tương phản cao, sắc nét.
* **Muted Text (`#64748B`):** Dùng cho nhãn, phụ đề và trục biểu đồ.
* **Precision Accent (`#0F766E`):** Tone xanh Teal trầm làm điểm nhấn duy nhất cho dữ liệu quan trọng.
* **Typography:** `Plus Jakarta Sans` cho văn bản điều hướng và `JetBrains Mono` cho con số tài chính.

---

## Mã nguồn Python (`app.py`)

```python
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# ---------------------------------------------------------
# 1. PAGE CONFIG & CUSTOM CSS INJECTION
# ---------------------------------------------------------
st.set_page_config(
    page_title="Executive Revenue Intelligence",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def inject_minimal_css():
    st.markdown("""
    <style>
        /* Import Google Fonts */
        @import url('[https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@500&display=swap](https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@500&display=swap)');

        /* Root CSS Variables */
        :root {
            --bg-color: #F8FAFC;
            --surface-color: #FFFFFF;
            --border-color: #E2E8F0;
            --text-primary: #0F172A;
            --text-muted: #64748B;
            --accent-color: #0F766E;
            --positive-color: #15803D;
            --negative-color: #B91C1C;
        }

        /* Reset Page Background & Typography */
        html, body, [class*="css"] {
            font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
            color: var(--text-primary);
            background-color: var(--bg-color);
        }

        .stApp {
            background-color: var(--bg-color);
        }

        /* Container Margins */
        .main .block-container {
            padding-top: 2.5rem;
            padding-bottom: 3rem;
            max-width: 1280px;
        }

        /* Custom Card Component */
        .metric-card {
            background-color: var(--surface-color);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 1.25rem 1.5rem;
            height: 100%;
        }

        .metric-label {
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-muted);
            margin-bottom: 0.5rem;
        }

        .metric-value {
            font-family: 'JetBrains Mono', monospace;
            font-size: 2rem;
            font-weight: 600;
            color: var(--text-primary);
            line-height: 1.2;
            margin-bottom: 0.5rem;
        }

        .metric-delta {
            font-size: 0.8125rem;
            font-weight: 500;
        }

        .delta-positive { color: var(--positive-color); }
        .delta-negative { color: var(--negative-color); }
        .delta-neutral { color: var(--text-muted); }

        /* Typography Customization */
        h1, h2, h3 {
            color: var(--text-primary) !important;
            font-weight: 700 !important;
            letter-spacing: -0.02em !important;
        }

        /* Hide Streamlit Chrome */
        #MainMenu, footer, header { visibility: hidden; }

        /* Style Selectbox Inputs */
        div[data-baseweb="select"] > div {
            background-color: var(--surface-color);
            border-color: var(--border-color);
            border-radius: 6px;
        }
    </style>
    """, unsafe_allow_html=True)

inject_minimal_css()

# ---------------------------------------------------------
# 2. MOCK DATA GENERATION
# ---------------------------------------------------------
np.random.seed(42)
dates = pd.date_range(start="2026-01-01", periods=12, freq="ME")
revenue = np.linspace(180, 240, 12) + np.random.normal(0, 5, 12)
expenses = revenue * 0.65 + np.random.normal(0, 3, 12)

df = pd.DataFrame({
    "Month": dates.strftime("%b %Y"),
    "Revenue": np.round(revenue * 10000, -2),
    "Expenses": np.round(expenses * 10000, -2)
})
df["Net Margin"] = df["Revenue"] - df["Expenses"]

# ---------------------------------------------------------
# 3. HEADER SECTION
# ---------------------------------------------------------
col_header, col_filter = st.columns([3, 1])

with col_header:
    st.markdown("<h1 style='margin:0; font-size: 1.75rem;'>Enterprise Revenue Intelligence</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: var(--text-muted); font-size: 0.875rem; margin-top: 4px;'>Financial performance and operating margin analytics</p>", unsafe_allow_html=True)

with col_filter:
    timeframe = st.selectbox("Timeframe", ["Fiscal Year 2026", "Fiscal Year 2025", "Trailing 12 Months"], label_visibility="collapsed")

st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

# ---------------------------------------------------------
# 4. METRIC CARDS (ZERO-ICON, TYPOGRAPHIC FOCUS)
# ---------------------------------------------------------
m1, m2, m3 = st.columns(3)

with m1:
    st.markdown("""
        <div class="metric-card">
            <div class="metric-label">Gross Revenue</div>
            <div class="metric-value">$2,548,200</div>
            <div class="metric-delta delta-positive">+14.2% vs previous period</div>
        </div>
    """, unsafe_allow_html=True)

with m2:
    st.markdown("""
        <div class="metric-card">
            <div class="metric-label">Operating Margin</div>
            <div class="metric-value">34.8%</div>
            <div class="metric-delta delta-positive">+2.1% efficiency yield</div>
        </div>
    """, unsafe_allow_html=True)

with m3:
    st.markdown("""
        <div class="metric-card">
            <div class="metric-label">Net Operating Expense</div>
            <div class="metric-value">$1,661,400</div>
            <div class="metric-delta delta-negative">+4.8% inflation variance</div>
        </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='height: 32px;'></div>", unsafe_allow_html=True)

# ---------------------------------------------------------
# 5. CHARTS & DATA PRESENTATION
# ---------------------------------------------------------
c_left, c_right = st.columns([2, 1])

with c_left:
    st.markdown("<h3 style='font-size: 1.125rem; margin-bottom: 16px;'>Revenue vs. Expenses Trend</h3>", unsafe_allow_html=True)
    
    # Plotly minimal styling
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df["Month"], y=df["Revenue"],
        name="Revenue",
        line=dict(color="#0F766E", width=2.5),
        mode="lines"
    ))
    
    fig.add_trace(go.Scatter(
        x=df["Month"], y=df["Expenses"],
        name="Expenses",
        line=dict(color="#94A3B8", width=1.5, dash="dash"),
        mode="lines"
    ))

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=10, b=0),
        height=320,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=12, color="#64748B")
        ),
        xaxis=dict(
            showgrid=False,
            showline=True,
            linecolor="#E2E8F0",
            tickfont=dict(color="#64748B", size=11)
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="#F1F5F9",
            showline=False,
            tickfont=dict(color="#64748B", size=11),
            tickprefix="$"
        ),
        hovermode="x unified"
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with c_right:
    st.markdown("<h3 style='font-size: 1.125rem; margin-bottom: 16px;'>Regional Contribution</h3>", unsafe_allow_html=True)
    
    region_data = pd.DataFrame({
        "Region": ["North America", "EMEA", "Asia Pacific", "Latin America"],
        "Share": ["42.5%", "28.1%", "21.4%", "8.0%"],
        "Growth": ["+12%", "+8%", "+18%", "+3%"]
    })
    
    st.dataframe(
        region_data,
        column_config={
            "Region": st.column_config.TextColumn("Region"),
            "Share": st.column_config.TextColumn("Revenue Share"),
            "Growth": st.column_config.TextColumn("YoY Delta")
        },
        hide_index=True,
        use_container_width=True
    )