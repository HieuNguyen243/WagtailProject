# 📊 Wagtail CRM — AI Business Intelligence & Analytics Dashboard

Hệ thống quản trị khách hàng & bán hàng (**CRM**) tích hợp **Machine Learning Offline** và **Apache Superset BI Dashboard** theo thời gian thực, xây dựng trên nền tảng **Wagtail CMS 8.0** & **Django 6.1**.

Dự án cung cấp giải pháp phân tích dữ liệu 360 độ: từ quản lý phễu bán hàng (Kanban Pipeline), hồ sơ khách hàng 360°, đến các mô hình AI dự báo doanh thu chuỗi thời gian (Ridge Regression 7 ngày) và phân khúc khách hàng RFM (K-Means Clustering).

---

## 📑 Mục Lục
1. [Yêu cầu hệ thống](#-yêu-cầu-hệ-thống)
2. [Bước 1: Thiết lập môi trường (Environment Setup)](#bước-1-thiết-lập-môi-trường-environment-setup)
3. [Bước 2: Khởi tạo Cơ sở dữ liệu (Database Setup)](#bước-2-khởi-tạo-cơ-sở-dữ-liệu-database-setup)
4. [Bước 3: Huấn luyện Mô hình Machine Learning (AI Training)](#bước-3-huấn-luyện-mô-hình-machine-learning-ai-training)
5. [Bước 4: Khởi chạy Dự án & Trải nghiệm](#bước-4-khởi-chạy-dự-án--trải-nghiệm)
6. [Bước 5: Tích hợp Apache Superset với CSDL SQLite & Tạo Dashboard](#bước-5-tích-hợp-apache-superset-với-csdl-sqlite--tạo-dashboard)
7. [Bảng đường dẫn URL & Tài khoản mặc định](#-bảng-đường-dẫn-url--tài-khoản-mặc-định)
8. [Khắc phục sự cố thường gặp (Troubleshooting)](#-khắc-phục-sự-cố-thường-gặp-troubleshooting)

---

## 💻 Yêu cầu hệ thống

* **Python:** Phiên bản 3.10, 3.11 hoặc 3.12 (khuyên dùng Python 3.11 / 3.12).
* **Git:** Để clone mã nguồn.
* **Docker Desktop:** *(Tùy chọn)* Chỉ cần cài đặt nếu bạn muốn dựng máy chủ **Apache Superset** nâng cao. Nếu chỉ sử dụng Wagtail CRM và AI Dashboard nội bộ (Chart.js), bạn **không cần Docker**.

---

## Bước 1: Thiết lập môi trường (Environment Setup)

### 1.1. Clone mã nguồn về máy
```bash
git clone <URL_REPOSITORY>
cd WagtailPrj
```

### 1.2. Tạo môi trường ảo (Virtualenv)
- **Trên Windows (PowerShell):**
  ```powershell
  python -m venv crm_env
  .\crm_env\Scripts\Activate.ps1
  ```
  *(💡 Nếu gặp lỗi PowerShell chặn script, chạy lệnh: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` rồi kích hoạt lại)*

- **Trên Windows (Command Prompt - cmd):**
  ```cmd
  python -m venv crm_env
  crm_env\Scripts\activate.bat
  ```

- **Trên macOS / Linux:**
  ```bash
  python3 -m venv crm_env
  source crm_env/bin/activate
  ```

### 1.3. Cài đặt các thư viện phụ thuộc
Di chuyển vào thư mục ứng dụng `wagtail_crm` và cài đặt gói dependencies:
```bash
cd wagtail_crm
pip install --upgrade pip
pip install -r requirements.txt
```

### 1.4. Thiết lập file biến môi trường (`.env`)
Tạo file `.env` từ file mẫu `.env.example`:
- **Windows (PowerShell):**
  ```powershell
  Copy-Item .env.example .env
  ```
- **Linux / macOS:**
  ```bash
  cp .env.example .env
  ```
*File `.env` mặc định đã cấu hình sẵn cổng kết nối Superset `http://localhost:8088/superset/dashboard/11/?standalone=1`.*

---

## Bước 2: Khởi tạo Cơ sở dữ liệu (Database Setup)

Hệ thống sử dụng cơ sở dữ liệu SQLite mặc định (`db.sqlite3`) nằm ngay trong thư mục `wagtail_crm`, giúp người dùng không cần cài đặt SQL Server hay PostgreSQL phức tạp.

Chạy 2 lệnh sau để khởi tạo cấu trúc bảng và nạp bộ dữ liệu mẫu kinh doanh phong phú:
```bash
# 1. Chạy migrations để khởi tạo toàn bộ schema CSDL
python manage.py migrate

# 2. Nạp dữ liệu kinh doanh mẫu thực tế (Khách hàng, Sản phẩm, Đơn hàng, Leads, Tickets)
python manage.py seed_crm
```

> **Dữ liệu được nạp tự động bao gồm:**
> - Tài khoản quản trị cấp cao (**Admin**).
> - **35+** hồ sơ khách hàng đầy đủ phân hạng (Standard, Silver, Gold, Platinum).
> - **150+** đơn hàng phân bổ 90 ngày với nhiều hình thức thanh toán (MB eBanking, ShopeePay, MoMo, ZaloPay) và vận chuyển (SPX, J&T, GHTK).
> - **15+** sản phẩm phần mềm, thiết bị và dịch vụ.
> - **20+** cơ hội bán hàng trên phễu Leads.
> - **45+** nhật ký tương tác và **24+** phiếu yêu cầu hỗ trợ khách hàng (Support Tickets).

---

## Bước 3: Huấn luyện Mô hình Machine Learning (AI Training)

Dự án tích hợp bộ máy Machine Learning **chạy Offline 100%** bằng `scikit-learn`, `pandas`, `numpy` gồm 2 mô hình:
1. **Time-Series Revenue Forecasting (Ridge Regression):** Phân tích xu hướng tăng trưởng và chu kỳ mùa vụ theo tuần, dự báo doanh thu 7 ngày tiếp theo (1 tuần tới để hạn chế tối đa sai số tích lũy) kèm khoảng tin cậy 95% (Lower/Upper Bound).
2. **Customer Segmentation & Churn Risk (RFM + K-Means Clustering):** Phân tích 3 chỉ số Recency - Frequency - Monetary, phân 4 nhóm khách hàng và ước lượng rủi ro rời bỏ (Churn Probability).

### Cách 1: Huấn luyện qua dòng lệnh CLI (Khuyên dùng)
```bash
python manage.py run_ai_models --days 7 --clusters 4
```
Lệnh sẽ tính toán và tự động lưu kết quả vào 2 bảng CSDL: `crm_revenueforecast` và `crm_customersegment`.

### Cách 2: Huấn luyện trực quan trên Web
1. Khởi động server (xem Bước 4).
2. Đăng nhập vào trang quản trị và truy cập menu **"Dự Báo & Phân Tích AI"** (`/admin/ai-models/`).
3. Nhấp nút **"Huấn Luyện Lại Mô Hình"** ở góc trên màn hình.

---

## Bước 4: Khởi chạy Dự án & Trải nghiệm

Khởi động máy chủ Django phát triển:
```bash
python manage.py runserver
```

Mở trình duyệt web và truy cập vào:
👉 **[http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)**

Đăng nhập bằng tài khoản quản trị mặc định:
* **Username:** `admin`
* **Password:** `admin`

---

## Bước 5: Tích hợp Apache Superset với CSDL SQLite & Tạo Dashboard

> **Giả định:** Bạn đã có một máy chủ Apache Superset đang chạy (ví dụ tại `http://localhost:8088`) và đã có tài khoản để đăng nhập vào Superset (mặc định: `admin` / `admin`).

### 5.1. Mount file CSDL SQLite (`db.sqlite3`) vào Apache Superset

Để Superset có thể đọc trực tiếp các bảng dữ liệu CRM và kết quả dự báo AI, container Superset cần được mount file `db.sqlite3` của dự án:

- **Trường hợp 1: Khởi chạy container mới bằng Docker**
  Mở terminal tại thư mục `wagtail_crm` và chạy lệnh mount volume:
  - **Trên Windows (PowerShell):**
    ```powershell
    docker run -d --name superset -p 8088:8088 `
      -v "${PWD}\db.sqlite3:/app/db.sqlite3" `
      -v "${PWD}\superset_config_docker.py:/app/pythonpath/superset_config.py" `
      apache/superset
    ```
  - **Trên Linux / macOS:**
    ```bash
    docker run -d --name superset -p 8088:8088 \
      -v "$(pwd)/db.sqlite3:/app/db.sqlite3" \
      -v "$(pwd)/superset_config_docker.py:/app/pythonpath/superset_config.py" \
      apache/superset
    ```

- **Trường hợp 2: Container Superset đã đang chạy sẵn**
  Nếu bạn đã có sẵn container Superset đang hoạt động mà chưa mount volume, hãy sao chép trực tiếp file database và file cấu hình vào container:
  ```bash
  # 1. Copy file database SQLite vào thư mục /app bên trong container
  docker cp db.sqlite3 superset:/app/db.sqlite3

  # 2. (Khuyên dùng) Copy file cấu hình để cho phép nhúng iframe vào Wagtail không bị chặn CSP
  docker cp superset_config_docker.py superset:/app/pythonpath/superset_config.py
  docker restart superset
  ```

---

### 5.2. Kết nối Database SQLite với Superset

#### Cách 1: Tự động hoàn toàn bằng Script (Khuyên dùng)
Bạn chỉ cần mở terminal tại thư mục `wagtail_crm` và chạy script tự động hóa:
```bash
python create_superset_dashboard.py
```
*Script sử dụng Superset REST API để tự động kết nối SQLite (`/app/db.sqlite3`), đăng ký 6 Datasets và dựng sẵn 7 biểu đồ phân tích.*

#### Cách 2: Kết nối thủ công qua giao diện Superset Web
1. Đăng nhập vào Superset tại **`http://localhost:8088`**.
2. Trên thanh menu trên cùng, vào **Settings (⚙️)** ➔ chọn **Database Connections** (hoặc nhấn nút **+ ➔ Data ➔ Connect database**).
3. Chọn hệ quản trị: **SQLite**.
4. Điền các trường thông tin:
   * **DISPLAY NAME:** `Wagtail CRM Database`
   * **SQLALCHEMY URI:**
     ```text
     sqlite:////app/db.sqlite3
     ```
     *(Lưu ý: Có đúng 4 dấu gạch chéo `////` để chỉ đường dẫn tuyệt đối `/app/db.sqlite3` trong Linux container).*
5. Nhấn **Test Connection**. Khi hiển thị thông báo *"Connection looks good!"*, bấm **Connect** để hoàn tất.

---

### 5.3. Tạo 7 Biểu đồ & Dashboard phân tích hoàn chỉnh

Sau khi file database đã được mount và kết nối, chạy script sau để tự động tạo và sắp xếp Dashboard với layout chuẩn:
```bash
python update_superset_dashboard_perfect.py
```

Script sẽ tự động cấu hình và gom các biểu đồ vào **Dashboard ID = 11**:
* **5 Biểu đồ phân tích CRM:** Xu hướng doanh thu theo thời gian, Phễu chuyển đổi Leads, Cơ cấu thanh toán & vận chuyển, Top sản phẩm bán chạy, Phân bổ phiếu hỗ trợ CSKH.
* **2 Biểu đồ Machine Learning AI:** Dự báo doanh thu 7 ngày tới (Ridge Regression + KTC 95%) và Phân khúc khách hàng RFM (K-Means Clustering).

---

### 5.4. Xem Dashboard nhúng trực tiếp trong Wagtail CRM

Truy cập trang quản trị Wagtail CRM để trải nghiệm Dashboard đã được nhúng qua iframe bảo mật:
👉 **[http://127.0.0.1:8000/admin/superset/](http://127.0.0.1:8000/admin/superset/)**

*Hỗ trợ đầy đủ tính năng: Tương tác bộ lọc thời gian thực, chế độ xem toàn màn hình (Fullscreen) và khả năng tùy chỉnh URL Dashboard.*

---

## 🌐 Bảng đường dẫn URL & Tài khoản mặc định

| Module | URL | Chức năng chính |
|---|---|---|
| 🤖 **Mô hình AI (Native)** | `http://127.0.0.1:8000/admin/ai-models/` | Xem trực quan biểu đồ dự báo doanh thu 7 ngày & cụm RFM vẽ bằng Chart.js (chuẩn FE-Skill, không cần Superset) |
| 📊 **Superset BI Dashboard** | `http://127.0.0.1:8000/admin/superset/` | Xem Dashboard 7 biểu đồ nhúng từ Apache Superset qua iframe |
| 🎯 **Phễu Bán Hàng (Kanban)** | `http://127.0.0.1:8000/admin/pipeline/` | Kéo thả quản lý trạng thái khách hàng tiềm năng (Leads), chuyển đổi thành khách hàng |
| 👤 **Hồ sơ Khách hàng 360°** | `http://127.0.0.1:8000/admin/customers/1/360/` | Xem lịch sử đơn hàng, nhật ký tương tác, thanh tiến độ thăng hạng VIP |
| 🦅 **Wagtail Admin** | `http://127.0.0.1:8000/admin/` | Quản lý CMS, danh mục sản phẩm, khách hàng, đơn hàng, snippets |
| 🛠️ **Django Admin** | `http://127.0.0.1:8000/django-admin/` | Quản trị cơ sở dữ liệu Django thuần |

### 🔑 Thông tin đăng nhập mặc định:
* **Hệ thống Wagtail CRM:** `admin` / `admin`
* **Hệ thống Apache Superset:** `admin` / `admin`

---

## 🛠️ Công nghệ sử dụng (Tech Stack)

* **Backend Web Framework:** Django 6.1.1, Wagtail CMS 8.0
* **Data Science & Machine Learning:** Scikit-learn, Pandas, Numpy (Offline Engine)
* **Business Intelligence (BI):** Apache Superset, ECharts
* **Frontend Visualization:** Chart.js 4.4, Plus Jakarta Sans, JetBrains Mono, Vanilla CSS & HTML5 (FE-Skill Design)
* **Database:** SQLite mặc định (`db.sqlite3`)

---

## ❓ Khắc phục sự cố thường gặp (Troubleshooting)

1. **Lỗi `Activate.ps1 cannot be loaded because running scripts is disabled` trên Windows PowerShell:**
   * **Khắc phục:** Mở PowerShell với quyền User và chạy:
     ```powershell
     Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
     .\crm_env\Scripts\Activate.ps1
     ```

2. **Giao diện Dashboard AI báo "Chưa có dữ liệu dự báo":**
   * **Khắc phục:** Bạn cần chạy lệnh huấn luyện AI ít nhất một lần:
     ```bash
     python manage.py run_ai_models
     ```

3. **Apache Superset báo lỗi không kết nối được SQLite:**
   * **Khắc phục:** Đảm bảo đường dẫn URI có đủ 4 dấu gạch chéo `sqlite:////app/db.sqlite3` và file `db.sqlite3` đã được copy hoặc mount vào thư mục `/app` bên trong container.
