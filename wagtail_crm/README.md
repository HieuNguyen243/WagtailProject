# 📊 Wagtail CRM — AI Business Intelligence Dashboard

Hệ thống quản trị khách hàng & đơn hàng (**CRM**) tích hợp **Dashboard Phân tích Dữ liệu AI** thông minh theo thời gian thực trên nền tảng **Wagtail 8.0** & **Django 6.1**.

---

## ⚡ Hướng dẫn cài đặt & Chạy dự án (Quick Start)

Dành cho người mới clone repository về máy để khởi chạy nhanh nhất:

### Bước 1: Clone mã nguồn về máy
```bash
git clone <URL_REPOSITORY>
cd WagtailProject
```

---

### Bước 2: Tạo & Kích hoạt môi trường ảo (Virtualenv)

- **Trên Windows (PowerShell):**
  ```powershell
  python -m venv crm_env
  crm_env\Scripts\Activate.ps1
  ```
- **Trên macOS / Linux:**
  ```bash
  python3 -m venv crm_env
  source crm_env/bin/activate
  ```

---

### Bước 3: Cài đặt các thư viện cần thiết
```bash
cd wagtail_crm
pip install -r requirements.txt
```

---

### Bước 4: Cấu hình biến môi trường (`.env`)

Tạo file `.env` từ file mẫu `.env.example`:
- **Windows (PowerShell):**
  ```powershell
  Copy-Item .env.example .env
  ```
- **macOS / Linux:**
  ```bash
  cp .env.example .env
  ```

---

### Bước 5: Khởi tạo Database & Dữ liệu mẫu

Chạy 2 lệnh sau để tạo cấu trúc bảng và nạp sẵn **20 khách hàng, 50 đơn hàng** cùng tài khoản **Admin**:
```bash
python manage.py migrate
python manage.py seed_crm
```

---

### Bước 6: Khởi động Server
```bash
python manage.py runserver
```

---

## 🌐 Đường dẫn truy cập & Tài khoản đăng nhập

| Trang | Đường dẫn URL | Chức năng |
|---|---|---|
| 🤖 **AI Machine Learning** | `http://127.0.0.1:8000/admin/ai-models/` | Quản trị mô hình Ridge Regression (dự báo 30 ngày) & RFM K-Means |
| 📊 **Superset BI Dashboard** | `http://127.0.0.1:8000/admin/superset/` | Nhúng trực tiếp Apache Superset Dashboard vào Wagtail Admin |
| 🎯 **Phễu Bán Hàng** | `http://127.0.0.1:8000/admin/pipeline/` | Kanban Board quản lý cơ hội & giai đoạn chuyển đổi Leads |
| 🦅 **Wagtail Admin** | `http://127.0.0.1:8000/admin/` | Quản lý Khách hàng, Đơn hàng, Trang web |
| 🛠️ **Django Admin** | `http://127.0.0.1:8000/django-admin/` | Quản trị dữ liệu Django tiêu chuẩn |

### 🔑 Tài khoản mặc định:
- **Username:** `admin`
- **Password:** `admin`

---

## ✨ Tính năng nổi bật

### 1. 🤖 Bộ máy Machine Learning Cục bộ (Offline ML Engine)
- **Time-Series Revenue Forecasting:** Mô hình Ridge Regression phân tích xu hướng tăng trưởng và tính chu kỳ 7 ngày, dự báo doanh thu 30 ngày tiếp theo kèm khoảng tin cậy 95%.
- **Customer Segmentation (RFM + K-Means):** Tự động phân loại 4-5 nhóm khách hàng, tính xác suất rời bỏ (Churn Probability).
- **Lưu trữ CSDL trung tâm:** Kết quả phân tích được lưu vào các bảng `RevenueForecast` và `CustomerSegment`.

### 2. 👥 Quản lý Khách hàng 360 & Đơn hàng (Wagtail CRM)
- Thêm, sửa, xóa, tìm kiếm khách hàng, xem Customer 360 view.
- Theo dõi đơn hàng với trạng thái xử lý, cổng thanh toán và bên vận chuyển.
### 3. 📊 Apache Superset BI & AI Dashboard (7 Biểu Đồ Chuẩn Hóa)
Hệ thống Dashboard hoàn chỉnh tích hợp trên Apache Superset với bảng màu chủ đạo Xanh dương & Trắng, phông chữ lớn, viền nổi bật (border) ngăn cách rõ ràng giữa các biểu đồ:
- **🏢 5 Biểu đồ phân tích thực trạng doanh nghiệp:**
  1. 📈 *Xu hướng Doanh thu & Số đơn hàng theo thời gian* (ECharts Mixed Line)
  2. 🎯 *Phễu chuyển đổi khách hàng tiềm năng* (Sales Pipeline Funnel)
  3. 💳 *Cơ cấu doanh thu theo cổng thanh toán & nhà vận chuyển* (Sunburst Chart)
  4. 🏆 *Top sản phẩm & danh mục mang lại doanh thu cao nhất* (Treemap)
  5. 🛡️ *Phân bổ phiếu hỗ trợ CSKH theo mức độ ưu tiên & trạng thái* (Stacked Bar Chart)
- **🤖 2 Biểu đồ hiển thị kết quả mô hình AI:**
  6. 🤖 *Dự báo doanh thu 30 ngày tới* kèm khoảng tin cậy 95% (AI Ridge Regression Area Chart)
  7. 🤖 *Phân khúc khách hàng RFM & xác định nguy cơ rời bỏ* (K-Means Clustering Bubble Chart)
- **Tự động hóa toàn diện:** Chạy `python update_superset_dashboard_perfect.py` để cập nhật tự động toàn bộ 7 biểu đồ và bố cục Dashboard qua REST API.

---

## 🛠️ Công nghệ sử dụng (Tech Stack)

- **Backend:** Django 6.1, Wagtail CMS 8.0
- **Machine Learning / AI Engine:** Scikit-learn, Pandas, Numpy (Offline ML)
- **Frontend / UI:** Vanilla CSS & HTML5, Chart.js 4.4, Google Fonts (Plus Jakarta Sans, JetBrains Mono)
- **Database:** SQLite
- **Utils:** `python-dotenv`

---

## 🔒 Bảo mật & Quy tắc Git

- File `.env` đã được liệt kê trong `.gitignore` và **không bao giờ bị đẩy lên Git**.
- File `.env.example` cung cấp sẵn template mẫu để đồng đội dễ dàng cấu hình.
