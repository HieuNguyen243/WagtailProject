# Wagtail CRM

Hệ thống quản lý khách hàng (CRM) xây dựng trên nền tảng **Wagtail 8.0** và **Django 6.1**.

## Tính năng

- **Quản lý Khách hàng** — Thêm, sửa, xóa, tìm kiếm thông tin khách hàng (tên, email, SĐT).
- **Quản lý Đơn hàng** — Theo dõi đơn hàng với mã đơn, tổng tiền, phương thức thanh toán, đơn vị vận chuyển và trạng thái.
- **Tích hợp Wagtail Admin** — Toàn bộ giao diện quản trị nằm trong sidebar Wagtail dưới nhóm **"Quản lý CRM"**.

## Cấu trúc thư mục

```
wagtail_crm/
├── crm/                          # App CRM chính
│   ├── management/
│   │   └── commands/
│   │       └── seed_crm.py       # Lệnh tạo dữ liệu mẫu
│   ├── migrations/
│   ├── models.py                 # Models: Customer, Order + SnippetViewSet
│   └── ...
├── home/                         # Wagtail home page (mặc định)
├── search/                       # Wagtail search (mặc định)
├── wagtail_crm/                  # Cấu hình Django project
│   ├── settings/
│   │   ├── base.py
│   │   ├── dev.py
│   │   └── production.py
│   ├── urls.py
│   └── wsgi.py
├── manage.py
├── requirements.txt
└── README.md
```

## Yêu cầu hệ thống

- Python 3.12+
- pip

## Hướng dẫn cài đặt

### 1. Clone repository

```bash
git clone <repository-url>
cd wagtail_crm
```

### 2. Tạo và kích hoạt môi trường ảo

**Windows (PowerShell):**
```powershell
python -m venv crm_env
crm_env\Scripts\activate
```

**macOS / Linux:**
```bash
python3 -m venv crm_env
source crm_env/bin/activate
```

### 3. Cài đặt các gói phụ thuộc

```bash
pip install -r requirements.txt
```

### 4. Tạo cơ sở dữ liệu

Chạy migration để tạo toàn bộ bảng trong SQLite:

```bash
python manage.py migrate
```

### 5. Tạo dữ liệu mẫu và tài khoản admin

Lệnh này sẽ tự động tạo:
- **1 tài khoản superuser** (username: `admin`, password: `admin`)
- **20 khách hàng** mẫu
- **50 đơn hàng** mẫu

```bash
python manage.py seed_crm
```

> **Ghi chú:** Lệnh sử dụng `get_or_create` nên có thể chạy nhiều lần mà không bị trùng dữ liệu.

### 6. Chạy server

```bash
python manage.py runserver
```

Truy cập:
- **Trang chủ:** [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Trang quản trị Wagtail:** [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

## Sử dụng

Sau khi đăng nhập vào trang quản trị, tìm mục **"Quản lý CRM"** trên sidebar trái:

| Mục | Chức năng |
|---|---|
| **Khách hàng** | Xem, thêm, sửa, xóa, tìm kiếm khách hàng theo tên / email / SĐT |
| **Đơn hàng** | Xem, thêm, sửa, xóa, tìm kiếm đơn hàng theo mã ĐH / tên KH |

### Phương thức thanh toán hỗ trợ

- MB eBanking
- ShopeePay
- ZaloPay
- MoMo

### Đơn vị vận chuyển hỗ trợ

- SPX Express
- J&T Express
- GHTK

### Trạng thái đơn hàng

- `pending` — Đang xử lý
- `completed` — Hoàn thành

## Tech Stack

| Thành phần | Phiên bản |
|---|---|
| Python | 3.12+ |
| Django | 6.1.x |
| Wagtail | 8.0.x |
| Database | SQLite (mặc định) |
