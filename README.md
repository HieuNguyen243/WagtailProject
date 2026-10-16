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
| 🦅 **Wagtail Admin** | `http://127.0.0.1:8000/admin/` | Quản lý Khách hàng, Đơn hàng, Trang web, Snippets AI |
| 🛠️ **Django Admin** | `http://127.0.0.1:8000/django-admin/` | Quản trị dữ liệu Django tiêu chuẩn |

### 🔑 Tài khoản mặc định:
- **Username:** `admin`
- **Password:** `admin`

---

## 🤖 Lệnh Kích Hoạt Pipeline Machine Learning (CLI)

Chạy huấn luyện và dự báo AI ngoại tuyến không phụ thuộc internet:
```bash
python manage.py run_ai_models --days 30 --clusters 4
```
Lệnh trên sẽ:
1. Đọc lịch sử bán hàng `Order`, huấn luyện mô hình **Ridge Time-Series Regression** và xuất dự báo 30 ngày tới kèm dải tin cậy 95% vào bảng `RevenueForecast`.
2. Phân tích chỉ số **RFM** của từng khách hàng, chuẩn hóa dữ liệu và phân cụm **K-Means**, tính toán điểm rủi ro rời bỏ (**Churn Risk**) và lưu vào bảng `CustomerSegment`.
3. Toàn bộ dữ liệu được lưu chuẩn hóa trong CSDL, sẵn sàng cho **Apache Superset** kết nối vẽ biểu đồ.

---

## ✨ Tính năng nổi bật

### 1. 🤖 Bộ máy Machine Learning Cục bộ (Offline ML Engine)
- **Time-Series Revenue Forecasting:** Mô hình Ridge Regression phân tích xu hướng tăng trưởng và tính chu kỳ 7 ngày (Seasonality), dự báo doanh thu 30 ngày tiếp theo kèm khoảng tin cậy 95% (Lower Bound - Upper Bound).
- **Customer Segmentation (RFM + K-Means):** Tự động phân loại 4-5 nhóm khách hàng thực tế (*VIP/Champions, Khách hàng trung thành, Tiềm năng, Có nguy cơ rời bỏ, Ngủ đông*), tính xác suất rời bỏ (Churn Probability) và gợi ý chiến lược chăm sóc tự động.
- **Lưu trữ CSDL trung tâm:** Kết quả phân tích được lưu vĩnh viễn vào các bảng `RevenueForecast` và `CustomerSegment`.

### 2. 📊 Tích hợp & Nhúng Apache Superset vào Wagtail Admin
- Giao diện nhúng trực tiếp Apache Superset Dashboard vào Wagtail qua iframe bảo mật.
- Hỗ trợ xem toàn màn hình (Fullscreen), tùy chỉnh URL Dashboard và hướng dẫn tạo biểu đồ từ bảng `crm_revenueforecast` và `crm_customersegment`.

### 3. 🎯 Quản lý Khách hàng 360 & Phễu Bán Hàng (CRM)
- **Kanban Pipeline:** Kéo thả cập nhật trạng thái leads (Mới, Đã liên hệ, Đạt điều kiện, Báo giá, Chốt thành công, Thất bại).
- **Customer 360 View:** Hồ sơ toàn diện khách hàng, lịch sử đơn hàng, chỉ số phân khúc RFM và rủi ro rời bỏ.

---

## 🛠️ Công nghệ sử dụng (Tech Stack)

- **Backend:** Django 6.1, Wagtail CMS 8.0
- **Machine Learning / Data Engine:** Scikit-learn, Pandas, Numpy (Offline ML)
- **BI & Visualizations:** Apache Superset Integration, Chart.js 4.4, Plus Jakarta Sans, JetBrains Mono
- **Database:** SQLite / PostgreSQL (Supabase compatible)
- **Utils:** `python-dotenv`

---

## 🔒 Bảo mật & Quy tắc Git

- File `.env` đã được liệt kê trong `.gitignore` và **không bao giờ bị đẩy lên Git**.
- File `.env.example` cung cấp sẵn template mẫu để đồng đội dễ dàng cấu hình.
