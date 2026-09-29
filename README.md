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

Mở file `.env` và thêm API key Gemini:
```env
GOOGLE_AI_API_KEY=your_gemini_api_key_here
```
> 💡 **Lưu ý:** Lấy key miễn phí trong 30 giây tại [Google AI Studio](https://aistudio.google.com/app/apikey). Nếu chưa có key, hệ thống vẫn tự động chạy và tính toán chỉ số dựa trên bộ máy phân tích CRM nội bộ.

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
| 📊 **AI Dashboard** | `http://127.0.0.1:8000/admin/ai-report/` | Báo cáo phân tích KPI, Biểu đồ & Chiến lược AI |
| 🦅 **Wagtail Admin** | `http://127.0.0.1:8000/admin/` | Quản lý Khách hàng, Đơn hàng, Trang web |
| 🛠️ **Django Admin** | `http://127.0.0.1:8000/django-admin/` | Quản trị dữ liệu Django tiêu chuẩn |

### 🔑 Tài khoản mặc định:
- **Username:** `admin`
- **Password:** `admin`

---

## ✨ Tính năng nổi bật

### 1. 📈 Dashboard Phân tích Kinh doanh AI
- **4 Thẻ KPI Realtime:** Tổng doanh thu, Tổng đơn hàng, Giá trị đơn trung bình (AOV), Tỷ lệ hoàn thành.
- **3 Biểu đồ trực quan tương tác (Chart.js 4.4):**
  - *Doughnut Chart:* Cơ cấu doanh thu theo phương thức thanh toán (MB eBanking, ShopeePay, ZaloPay, MoMo).
  - *Pie Chart:* Tỷ lệ trạng thái đơn hàng (Hoàn thành / Đang xử lý).
  - *Bar Chart:* Phân bổ doanh số theo các đơn vị vận chuyển (SPX Express, GHTK, J&T Express).
- **Phân tích Chiến lược & Đề xuất hành động:**
  - Gemini AI trích xuất nhận định định lượng theo từng chủ đề (*Dòng tiền, Logistics, Khách hàng...*).
  - Đề xuất giải pháp hành động kèm mức độ ưu tiên (*Ưu tiên cao, Chiến lược, Tối ưu*).
- **Bảng Khách hàng VIP:** Avatar chữ cái viết tắt, thanh tỷ trọng đóng góp doanh thu, tự động gắn nhãn phân hạng (*✨ Platinum, 👑 Gold, 💎 Thân thiết*).
- **Tìm kiếm tức thì:** Lọc trực tiếp khách hàng theo tên, email, hạng thành viên ngay trên giao diện.
- **Tiện ích xuất báo cáo:** Hỗ trợ In ra file **PDF chuẩn A4** và **Sao chép nội dung Insight** vào Clipboard.

### 2. 👥 Quản lý Khách hàng & Đơn hàng (Wagtail CRM)
- Thêm, sửa, xóa, tìm kiếm khách hàng.
- Theo dõi đơn hàng với trạng thái xử lý, cổng thanh toán và bên vận chuyển.

---

## 🛠️ Công nghệ sử dụng (Tech Stack)

- **Backend:** Django 6.1, Wagtail CMS 8.0
- **AI Engine:** Google Gemini AI REST API (`gemini-3.5-flash-lite`, `gemini-3.8-flash`)
- **Frontend / UI:** Vanilla CSS & HTML5, Chart.js 4.4, Google Fonts (Plus Jakarta Sans, JetBrains Mono)
- **Database:** SQLite
- **Network & Utils:** `httpx`, `python-dotenv`

---

## 🔒 Bảo mật & Quy tắc Git

- File `.env` chứa API key thật đã được liệt kê trong `.gitignore` và **không bao giờ bị đẩy lên Git**.
- File `.env.example` cung cấp sẵn template mẫu để đồng đội dễ dàng cấu hình.
- Hệ thống hỗ trợ **Fallback mượt mà**: Nếu không có API Key hoặc mất mạng, trang Dashboard vẫn tự động hiển thị đầy đủ biểu đồ và báo cáo từ CSDL nội bộ.
