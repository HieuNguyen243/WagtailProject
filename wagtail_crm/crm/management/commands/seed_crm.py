# crm/management/commands/seed_crm.py

import random
from decimal import Decimal
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from crm.models import (
    Customer,
    Order,
    OrderItem,
    Product,
    Lead,
    Interaction,
    SupportTicket,
)
from crm.ai_engine import run_all_ai_pipeline

User = get_user_model()


class Command(BaseCommand):
    help = "Tạo dữ liệu mẫu đa dạng cho CRM (35 khách hàng, 150 đơn hàng trải dài 90 ngày, Leads, Tickets, Tương tác) và huấn luyện AI"

    # ── 1. Danh mục sản phẩm & dịch vụ ─────────────────────────
    PRODUCTS = [
        # Phần mềm & Dịch vụ
        {
            "name": "CRM Cloud Starter (Gói 5 Users / Năm)",
            "sku": "SOFT-CRM-01",
            "category": "software",
            "price": Decimal("3500000"),
            "status": "active",
            "description": "Hệ thống quản lý khách hàng và bán hàng trên nền tảng đám mây cho doanh nghiệp nhỏ.",
        },
        {
            "name": "CRM Cloud Enterprise (Không giới hạn Users)",
            "sku": "SOFT-CRM-02",
            "category": "software",
            "price": Decimal("12000000"),
            "status": "active",
            "description": "Giải pháp CRM cao cấp tích hợp AI, phân quyền đa chi nhánh và API mở.",
        },
        {
            "name": "ERP Next Integration Pack",
            "sku": "SOFT-ERP-01",
            "category": "software",
            "price": Decimal("8500000"),
            "status": "active",
            "description": "Gói kết nối và đồng bộ tự động dữ liệu kho, kế toán và đơn hàng ERP.",
        },
        {
            "name": "AI Customer Insights Module",
            "sku": "SOFT-AI-01",
            "category": "software",
            "price": Decimal("5000000"),
            "status": "active",
            "description": "Phân hệ trợ lý AI phân tích hành vi mua sắm và dự báo doanh số chuyên sâu.",
        },
        # Khóa học đào tạo
        {
            "name": "Khóa đào tạo Kỹ năng Bán hàng B2B Thực chiến",
            "sku": "EDU-B2B-01",
            "category": "course",
            "price": Decimal("2200000"),
            "status": "active",
            "description": "Chương trình huấn luyện 6 tuần dành cho chuyên viên phát triển thị trường.",
        },
        {
            "name": "Khóa học Business Intelligence & Phân tích Dữ liệu",
            "sku": "EDU-BI-01",
            "category": "course",
            "price": Decimal("4500000"),
            "status": "active",
            "description": "Làm chủ quy trình xây dựng Dashboard trực quan và phân tích dữ liệu kinh doanh.",
        },
        {
            "name": "Khóa học CSKH & Nghệ thuật Giữ chân Khách hàng",
            "sku": "EDU-CSKH-01",
            "category": "course",
            "price": Decimal("1800000"),
            "status": "active",
            "description": "Quy trình chăm sóc và giải quyết khiếu nại khách hàng chuyên nghiệp.",
        },
        # Thiết bị công nghệ
        {
            "name": "Máy POS bán hàng cảm ứng để bàn Sunmi D2",
            "sku": "HW-POS-01",
            "category": "hardware",
            "price": Decimal("5800000"),
            "status": "active",
            "description": "Màn hình cảm ứng 15.6 inch, cấu hình cao, chạy mượt mà các ứng dụng bán hàng.",
        },
        {
            "name": "Máy in hóa đơn nhiệt siêu tốc Xprinter XP-Q800",
            "sku": "HW-PRN-01",
            "category": "hardware",
            "price": Decimal("1350000"),
            "status": "active",
            "description": "Tốc độ in 260mm/s, khổ giấy K80, kết nối cổng LAN và USB.",
        },
        {
            "name": "Máy quét mã vạch không dây 2D Zebra DS2278",
            "sku": "HW-SCAN-01",
            "category": "hardware",
            "price": Decimal("2450000"),
            "status": "active",
            "description": "Quét nhanh mã vạch 1D và QR Code 2D từ xa với khoảng cách tới 15m.",
        },
        {
            "name": "Bộ định tuyến WiFi doanh nghiệp Ruijie Reyee RG-EW1200",
            "sku": "HW-WIFI-01",
            "category": "hardware",
            "price": Decimal("1950000"),
            "status": "active",
            "description": "Hỗ trợ 100 thiết bị kết nối đồng thời, ổn định và bảo mật cao.",
        },
        # Phụ kiện & Khác
        {
            "name": "Giấy in nhiệt K80 phi 45 (Thùng 50 cuộn)",
            "sku": "ACC-K80-50",
            "category": "accessory",
            "price": Decimal("350000"),
            "status": "active",
            "description": "Giấy in nhiệt chất lượng cao bọc bạc bảo quản lâu dài, không bụi giấy.",
        },
        {
            "name": "Thẻ nhựa PVC VIP Member (Hộp 100 thẻ)",
            "sku": "ACC-RFID-100",
            "category": "accessory",
            "price": Decimal("650000"),
            "status": "active",
            "description": "Thẻ tích điểm khách hàng thân thiết in ấn sắc nét chuẩn ISO.",
        },
        {
            "name": "Cáp chuyển đổi đa năng Type-C sang HDMI/LAN",
            "sku": "ACC-CAB-01",
            "category": "accessory",
            "price": Decimal("280000"),
            "status": "active",
            "description": "Vỏ nhôm tản nhiệt cao cấp, hỗ trợ xuất hình ảnh 4K sắc nét.",
        },
        {
            "name": "Chân đế kim loại chống rung cho máy quét mã vạch",
            "sku": "ACC-STD-01",
            "category": "accessory",
            "price": Decimal("150000"),
            "status": "active",
            "description": "Chân đế tiện lợi hỗ trợ chế độ quét tự động không cần bấm cò.",
        },
    ]

    # ── 2. Danh sách 35 khách hàng đa dạng ─────────────────────
    CUSTOMERS_DATA = [
        {"name": "Nguyễn Văn An", "email": "an.nguyen@gmail.com", "phone": "0901234567", "company": "Công ty CP Công nghệ Sao Việt", "address": "Tầng 5, Keangnam Landmark 72, Cầu Giấy, Hà Nội", "type": "b2b", "tier": "platinum"},
        {"name": "Trần Thị Bích", "email": "bich.tran@outlook.com", "phone": "0912345678", "company": "TNHH Dịch vụ Du lịch Biển Đông", "address": "128 Nguyễn Đình Chiểu, Quận 3, TP.HCM", "type": "b2b", "tier": "gold"},
        {"name": "Lê Hoàng Cường", "email": "cuong.le@yahoo.com", "phone": "0923456789", "company": "Chuỗi Bách Hóa Cường Phát", "address": "45 Lê Duẩn, Hải Châu, Đà Nẵng", "type": "b2b", "tier": "gold"},
        {"name": "Phạm Minh Đức", "email": "duc.pham@gmail.com", "phone": "0934567890", "company": "Cửa hàng Thiết bị Minh Đức", "address": "88 Quang Trung, Gò Vấp, TP.HCM", "type": "b2c", "tier": "silver"},
        {"name": "Hoàng Thị Em", "email": "em.hoang@hotmail.com", "phone": "0945678901", "company": "Thời Trang Hoàng Em", "address": "12 Phố Huế, Hoàn Kiếm, Hà Nội", "type": "b2c", "tier": "standard"},
        {"name": "Vũ Đình Phong", "email": "phong.vu@gmail.com", "phone": "0956789012", "company": "Công ty Logistics Toàn Cầu", "address": "Km 9, Xa lộ Hà Nội, TP. Thủ Đức, TP.HCM", "type": "b2b", "tier": "platinum"},
        {"name": "Đặng Thùy Giang", "email": "giang.dang@outlook.com", "phone": "0967890123", "company": "Nội Thất Tân Cổ Điển Giang Đặng", "address": "250 Nguyễn Văn Linh, Long Biên, Hà Nội", "type": "b2b", "tier": "silver"},
        {"name": "Bùi Quốc Hải", "email": "hai.bui@gmail.com", "phone": "0978901234", "company": "Nhà thuốc Tân Dược Quốc Hải", "address": "76 Trần Phú, TP. Nha Trang, Khánh Hòa", "type": "b2b", "tier": "gold"},
        {"name": "Ngô Thanh Inh", "email": "inh.ngo@yahoo.com", "phone": "0389012345", "company": "", "address": "104 Nguyễn Trãi, Thanh Xuân, Hà Nội", "type": "b2c", "tier": "standard"},
        {"name": "Đỗ Thị Kim", "email": "kim.do@gmail.com", "phone": "0370123456", "company": "Chuỗi Trà Sữa Kim Tea", "address": "15 Đinh Tiên Hoàng, Quận 1, TP.HCM", "type": "b2b", "tier": "platinum"},
        {"name": "Lý Văn Long", "email": "long.ly@outlook.com", "phone": "0361234567", "company": "Cơ khí Chính xác Long Lý", "address": "KCN Amata, TP. Biên Hòa, Đồng Nai", "type": "b2b", "tier": "silver"},
        {"name": "Trịnh Hồng Mai", "email": "mai.trinh@gmail.com", "phone": "0352345678", "company": "", "address": "33 Đại Cồ Việt, Hai Bà Trưng, Hà Nội", "type": "b2c", "tier": "silver"},
        {"name": "Cao Bảo Ngọc", "email": "ngoc.cao@hotmail.com", "phone": "0343456789", "company": "Nha Khoa Nụ Cười Xinh", "address": "82 Cách Mạng Tháng 8, Quận 10, TP.HCM", "type": "b2b", "tier": "gold"},
        {"name": "Phan Văn Oanh", "email": "oanh.phan@gmail.com", "phone": "0334567890", "company": "", "address": "19 Hùng Vương, TP. Huế, Thừa Thiên Huế", "type": "b2c", "tier": "standard"},
        {"name": "Dương Minh Phúc", "email": "phuc.duong@yahoo.com", "phone": "0325678901", "company": "Phúc Hưng Group", "address": "Tòa nhà Diamond Plaza, Lê Duẩn, Quận 1, TP.HCM", "type": "b2b", "tier": "platinum"},
        {"name": "Hồ Thị Quỳnh", "email": "quynh.ho@gmail.com", "phone": "0786789012", "company": "Mỹ Phẩm Xách Tay Quỳnh Ho", "address": "55 Bà Triệu, TP. Vũng Tàu, Bà Rịa - Vũng Tàu", "type": "b2c", "tier": "silver"},
        {"name": "Tô Đức Rạng", "email": "rang.to@outlook.com", "phone": "0777890123", "company": "Nông Sản Sạch Rạng Đông", "address": "40 Phan Đình Phùng, TP. Đà Lạt, Lâm Đồng", "type": "b2b", "tier": "gold"},
        {"name": "Mai Thanh Sơn", "email": "son.mai@gmail.com", "phone": "0768901234", "company": "", "address": "18 Trần Hưng Đạo, TP. Cần Thơ", "type": "b2c", "tier": "standard"},
        {"name": "Lưu Thị Tâm", "email": "tam.luu@hotmail.com", "phone": "0759012345", "company": "Trung Tâm Anh Ngữ Tâm Lưu", "address": "90 Láng Hạ, Đống Đa, Hà Nội", "type": "b2b", "tier": "silver"},
        {"name": "Châu Văn Uy", "email": "uy.chau@gmail.com", "phone": "0580123456", "company": "Nhà hàng Hải sản Uy Châu", "address": "32 Bạch Đằng, Hải Châu, Đà Nẵng", "type": "b2b", "tier": "gold"},
        # Khách hàng bổ sung mới
        {"name": "Tạ Quang Vũ", "email": "vu.ta@vietinsoft.com", "phone": "0982345678", "company": "Công ty TNHH Phần mềm VietinSoft", "address": "Tòa nhà FPT, Duy Tân, Cầu Giấy, Hà Nội", "type": "b2b", "tier": "platinum"},
        {"name": "Đoàn Thu Hà", "email": "ha.doan@gmail.com", "phone": "0973456789", "company": "Hệ thống Mẹ & Bé Hà Đoàn", "address": "215 Xã Đàn, Đống Đa, Hà Nội", "type": "b2c", "tier": "silver"},
        {"name": "Lương Thế Vinh", "email": "vinh.luong@vinhcorp.vn", "phone": "0964567890", "company": "Tập đoàn Đầu tư Thế Vinh", "address": "Landmark 81, Bình Thạnh, TP.HCM", "type": "b2b", "tier": "platinum"},
        {"name": "Phùng Ngọc Thảo", "email": "thao.phung@gmail.com", "phone": "0955678901", "company": "Tiệm Bánh Ngọt Thảo Bakery", "address": "14 Nguyễn Thị Minh Khai, Quận 1, TP.HCM", "type": "b2c", "tier": "standard"},
        {"name": "Quách Tấn Dũng", "email": "dung.quach@dungphat.com", "phone": "0946789012", "company": "Công ty Vật liệu Xây dựng Dũng Phát", "address": "KCN Sóng Thần, Dĩ An, Bình Dương", "type": "b2b", "tier": "gold"},
        {"name": "Lâm Hoài An", "email": "an.lam@hotmail.com", "phone": "0937890123", "company": "", "address": "56 Hùng Vương, TP. Pleiku, Gia Lai", "type": "b2c", "tier": "standard"},
        {"name": "Vương Triều Vĩ", "email": "vi.vuong@trieuvi.vn", "phone": "0928901234", "company": "Chuỗi Khách sạn Triều Vĩ Luxury", "address": "02 Trần Phú, TP. Nha Trang, Khánh Hòa", "type": "b2b", "tier": "platinum"},
        {"name": "Hà Kiều Trang", "email": "trang.ha@gmail.com", "phone": "0919012345", "company": "Trang Spa & Wellness", "address": "108 Pasteur, Bến Nghé, Quận 1, TP.HCM", "type": "b2c", "tier": "gold"},
        {"name": "Nghiêm Xuân Hùng", "email": "hung.nghiem@hungthinh.vn", "phone": "0900123456", "company": "Bảo hộ Lao động Hùng Thịnh", "address": "380 Quốc lộ 1A, Bình Chánh, TP.HCM", "type": "b2b", "tier": "silver"},
        {"name": "Diệp Bích Loan", "email": "loan.diep@yahoo.com", "phone": "0891234567", "company": "", "address": "72 Trần Hưng Đạo, Hoàn Kiếm, Hà Nội", "type": "b2c", "tier": "standard"},
        {"name": "Thái Khắc Huy", "email": "huy.thai@huyphat.vn", "phone": "0882345678", "company": "Công ty Vận tải Huy Phát", "address": "Cảng Đình Vũ, Hải An, Hải Phòng", "type": "b2b", "tier": "gold"},
        {"name": "Bhan Văn Khoa", "email": "khoa.bhan@gmail.com", "phone": "0873456789", "company": "Cửa hàng Điện thoại Khoa Mobile", "address": "150 Hoàng Diệu, Hải Châu, Đà Nẵng", "type": "b2c", "tier": "silver"},
        {"name": "Trầm Bửu Lộc", "email": "loc.tram@buuloc.com", "phone": "0864567890", "company": "TNHH Chế biến Thủy sản Bửu Lộc", "address": "KCN Sông Hậu, Châu Thành, Hậu Giang", "type": "b2b", "tier": "platinum"},
        {"name": "Cung Kim Chi", "email": "chi.cung@gmail.com", "phone": "0855678901", "company": "", "address": "89 Nguyễn Huệ, TP. Quy Nhơn, Bình Định", "type": "b2c", "tier": "standard"},
        {"name": "Âu Dương Phong", "email": "phong.auduong@taydoc.vn", "phone": "0846789012", "company": "Dược phẩm Tây Độc Group", "address": "Tầng 12, Keangnam Landmark 72, Hà Nội", "type": "b2b", "tier": "gold"},
    ]

    # ── 3. Danh sách 25 Leads tiềm năng ────────────────────────
    LEADS_DATA = [
        {"name": "Trần Bảo Nam", "company": "Công ty TNHH Smart Logistics", "email": "nam.tran@smartlog.vn", "phone": "0981112233", "source": "website", "status": "proposal", "value": Decimal("18000000"), "notes": "Cần triển khai CRM cho đội 25 nhân viên, quan tâm tích hợp API định vị GPS."},
        {"name": "Lê Thu Thảo", "company": "Chuỗi Cà Phê Mộc Xưa", "email": "thao.le@mocxua.com", "phone": "0972223344", "source": "social", "status": "qualified", "value": Decimal("12500000"), "notes": "Cần giải pháp máy POS và phần mềm quản lý thẻ VIP cho 4 chi nhánh."},
        {"name": "Vũ Quang Huy", "company": "Tập đoàn Xây dựng Hoàng Gia", "email": "huy.vu@hoanggia.vn", "phone": "0963334455", "source": "referral", "status": "contacted", "value": Decimal("35000000"), "notes": "Do anh Nguyễn Văn An giới thiệu. Cần nâng cấp hệ thống quản trị dữ liệu khách hàng B2B."},
        {"name": "Nguyễn Hoàng Yến", "company": "Trung tâm Đào tạo Kế toán Yến Nguyễn", "email": "yen@ketoanyen.edu.vn", "phone": "0954445566", "source": "website", "status": "won", "value": Decimal("8500000"), "notes": "Đã chốt hợp đồng đào tạo và mua phần mềm CRM Starter."},
        {"name": "Đỗ Đình Trọng", "company": "Công ty Phân phối Tiêu dùng Trọng Đỗ", "email": "trong@tieudungtrongdo.vn", "phone": "0945556677", "source": "cold_call", "status": "lost", "value": Decimal("15000000"), "notes": "Khách quyết định gia hạn phần mềm cũ vì chưa có ngân sách chuyển đổi."},
        {"name": "Bùi Mai Hương", "company": "Phòng khám Đa khoa Quốc tế An Sinh", "email": "huong.bui@ansinhclinic.vn", "phone": "0936667788", "source": "event", "status": "proposal", "value": Decimal("22000000"), "notes": "Gặp tại hội chợ TechExpo. Quan tâm giải pháp CRM Cloud Enterprise kết hợp nhắc lịch hẹn."},
        {"name": "Phạm Quốc Tuấn", "company": "Vận tải & Kho bãi Tuấn Kiệt", "email": "tuan@tuankiettrans.vn", "phone": "0927778899", "source": "website", "status": "new", "value": Decimal("9000000"), "notes": "Để lại thông tin trên form báo giá, cần nhân viên gọi tư vấn."},
        {"name": "Hoàng Lan Anh", "company": "Shop Thời trang Lan Anh Boutique", "email": "lananh@boutique.vn", "phone": "0918889900", "source": "social", "status": "contacted", "value": Decimal("4200000"), "notes": "Hỏi về máy in hóa đơn và máy quét mã vạch không dây."},
        {"name": "Võ Minh Khang", "company": "Học viện Lập trình TechKids", "email": "khang.vo@techkids.vn", "phone": "0909990011", "source": "referral", "status": "qualified", "value": Decimal("16000000"), "notes": "Cần mua khóa học phân tích dữ liệu cho 10 giảng viên và bộ công cụ BI."},
        {"name": "Trịnh Thu Hà", "company": "Công ty Luật Trịnh Gia", "email": "ha.trinh@trinhlaw.com", "phone": "0891113355", "source": "website", "status": "new", "value": Decimal("6500000"), "notes": "Yêu cầu bảo mật cao, cần hệ thống lưu trữ hồ sơ vụ việc khách hàng."},
        {"name": "Lương Gia Bảo", "company": "Hệ thống Siêu thị Tiện lợi 247", "email": "bao.luong@247mart.vn", "phone": "0882224466", "source": "event", "status": "won", "value": Decimal("48000000"), "notes": "Đã ký biên bản ghi nhớ trang bị 10 bộ POS và hệ thống CRM Cloud Enterprise."},
        {"name": "Đặng Quốc Việt", "company": "Gốm sứ Mỹ nghệ Bát Tràng Việt", "email": "viet@gomsubattrang.vn", "phone": "0873335577", "source": "other", "status": "lost", "value": Decimal("5000000"), "notes": "Quy mô hộ kinh doanh gia đình chưa phù hợp với giải pháp ERP/CRM."},
        {"name": "Tạ Ngọc Ánh", "company": "Hệ thống Salon Tóc Ánh Kim", "email": "anhkim@salontoc.vn", "phone": "0864446688", "source": "social", "status": "proposal", "value": Decimal("7500000"), "notes": "Đang xem xét bản chào giá gói CRM Starter + Module CSKH."},
        {"name": "Ngô Văn Quyền", "company": "Cửa hàng Xe máy Quyền Ngô", "email": "quyen@xemayquyen.com", "phone": "0855557799", "source": "cold_call", "status": "contacted", "value": Decimal("11000000"), "notes": "Quan tâm đến giải pháp quản lý lịch bảo dưỡng và nhắc nhở khách hàng qua tin nhắn."},
        {"name": "Lê Mỹ Dung", "company": "Công ty Cung ứng Thực phẩm Sạch Xanh", "email": "dung.le@thucphamxanh.vn", "phone": "0846668800", "source": "website", "status": "qualified", "value": Decimal("19000000"), "notes": "Cần tích hợp đơn hàng online và tự động xuất phiếu vận chuyển cho đối tác."},
        {"name": "Hoàng Khắc Nam", "company": "Nội thất Văn phòng Hiện Đại", "email": "nam.hoang@noithathiendai.vn", "phone": "0837779911", "source": "website", "status": "new", "value": Decimal("14000000"), "notes": "Tìm kiếm giải pháp phân quyền nhân viên bán hàng theo khu vực Bắc - Nam."},
        {"name": "Chu Đình Tùng", "company": "Thiết bị Y tế An Phát", "email": "tung.chu@anphatmed.vn", "phone": "0828880022", "source": "referral", "status": "proposal", "value": Decimal("26000000"), "notes": "Khách hàng của Bùi Quốc Hải giới thiệu. Cần hợp đồng triển khai trong tháng này."},
        {"name": "Bành Đức Trí", "company": "Chuỗi Nhà hàng Bò Tơ Trí Bành", "email": "tri@bototribanh.com", "phone": "0819991133", "source": "social", "status": "contacted", "value": Decimal("8000000"), "notes": "Cần 3 máy POS cảm ứng và phần mềm in bill cho nhà hàng mới mở tại Tân Bình."},
        {"name": "Quách Ái Nhi", "company": "Mỹ phẩm Thiên nhiên Nhi Nhi", "email": "nhinhi@naturalcos.vn", "phone": "0801112244", "source": "website", "status": "won", "value": Decimal("11500000"), "notes": "Chốt hợp đồng mua CRM Cloud Starter và gói phân tích AI Customer Insights."},
        {"name": "Thân Trọng Nghĩa", "company": "Tài chính & Thu hồi nợ Trọng Nghĩa", "email": "nghia@trongnghiafinance.vn", "phone": "0792223355", "source": "cold_call", "status": "lost", "value": Decimal("17000000"), "notes": "Yêu cầu tính năng gọi tự động VoIP phức tạp chưa có sẵn trong bản này."},
    ]

    PAYMENT_METHODS = ["MB_eBanking", "ShopeePay", "ZaloPay", "MoMo"]
    SHIPPING_PROVIDERS = ["SPX_Express", "J_and_T_Express", "GHTK"]

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING(">> Bắt đầu tạo bộ dữ liệu kinh doanh mẫu ĐA DẠNG & THỰC TẾ..."))

        # ── 1. Tạo tài khoản người dùng & Nhân viên kinh doanh ──────
        admin_user, _ = User.objects.get_or_create(
            username="admin",
            defaults={"email": "admin@crm.vn", "is_staff": True, "is_superuser": True},
        )
        if _:
            admin_user.set_password("admin")
            admin_user.save()
            self.stdout.write("   [OK] Superuser: admin / admin (đã tạo mới)")
        else:
            self.stdout.write("   [--] Superuser: admin (đã tồn tại)")

        sales_users = []
        sales_data = [
            {"username": "sales_an", "email": "sales.an@crm.vn", "first_name": "Nguyễn Văn", "last_name": "An"},
            {"username": "sales_binh", "email": "sales.binh@crm.vn", "first_name": "Trần Thị", "last_name": "Bình"},
            {"username": "sales_chi", "email": "sales.chi@crm.vn", "first_name": "Lê Hoàng", "last_name": "Chi"},
            {"username": "sales_dung", "email": "sales.dung@crm.vn", "first_name": "Phạm Quốc", "last_name": "Dũng"},
        ]
        for s in sales_data:
            user, created = User.objects.get_or_create(
                username=s["username"],
                defaults={
                    "email": s["email"],
                    "first_name": s["first_name"],
                    "last_name": s["last_name"],
                    "is_staff": True,
                },
            )
            if created:
                user.set_password("sales123")
                user.save()
            sales_users.append(user)

        self.stdout.write(f"   [OK] Đội ngũ Sales: {len(sales_users)} chuyên viên tư vấn")

        # ── 2. Tạo danh mục sản phẩm ───────────────────────────────
        products = []
        for p_info in self.PRODUCTS:
            prod, _ = Product.objects.update_or_create(
                sku=p_info["sku"],
                defaults=p_info,
            )
            products.append(prod)
        self.stdout.write(f"   [OK] Sản phẩm & Dịch vụ: {len(products)} sản phẩm sẵn sàng")

        # ── 3. Tạo 35 Khách hàng ────────────────────────────────────
        customers = []
        for c_info in self.CUSTOMERS_DATA:
            cust, _ = Customer.objects.update_or_create(
                email=c_info["email"],
                defaults={
                    "name": c_info["name"],
                    "phone": c_info["phone"],
                    "company": c_info["company"],
                    "address": c_info["address"],
                    "customer_type": c_info["type"],
                    "tier": c_info["tier"],
                    "assigned_to": random.choice(sales_users),
                },
            )
            customers.append(cust)
        self.stdout.write(f"   [OK] Hồ sơ Khách hàng: {len(customers)} khách hàng (B2B & B2C)")

        # ── 4. Tạo Khách hàng tiềm năng (Leads) ────────────────────
        now_time = timezone.now()
        leads_count = 0
        for idx, l_info in enumerate(self.LEADS_DATA):
            is_won = l_info["status"] == "won"
            conv_customer = customers[idx % len(customers)] if is_won else None
            conv_time = now_time - timedelta(days=random.randint(2, 30)) if is_won else None

            lead_obj, _ = Lead.objects.update_or_create(
                phone=l_info["phone"],
                defaults={
                    "name": l_info["name"],
                    "company": l_info["company"],
                    "email": l_info["email"],
                    "source": l_info["source"],
                    "status": l_info["status"],
                    "estimated_value": l_info["value"],
                    "notes": l_info["notes"],
                    "assigned_to": random.choice(sales_users),
                    "is_converted": is_won,
                    "converted_customer": conv_customer,
                    "converted_at": conv_time,
                },
            )
            leads_count += 1
        self.stdout.write(f"   [OK] Phễu bán hàng (Leads): {leads_count} cơ hội kinh doanh")

        # ── 5. Tạo 150 Đơn hàng ĐA DẠNG trải dài 90 ngày ───────────
        Order.objects.all().delete()

        order_notes_pool = [
            "Giao hàng giờ hành chính.",
            "Khách hàng thân thiết đề nghị kiểm tra kỹ sản phẩm trước khi giao.",
            "Xuất hóa đơn VAT điện tử gửi về email doanh nghiệp.",
            "Hỗ trợ cài đặt phần mềm từ xa qua Ultraviewer.",
            "Yêu cầu gọi trước 30 phút khi giao hàng.",
            "Đóng gói cẩn thận có dán tem hàng dễ vỡ.",
            "Giao cho bảo vệ tòa nhà nếu khách bận họp.",
            "Hợp đồng cung cấp định kỳ theo quý.",
        ]

        total_orders = 150
        created_orders = []

        # Phân bổ 150 đơn hàng trải dài trong 90 ngày gần đây
        # Có xu hướng tăng dần về gần hiện tại và có sự chênh lệch giữa ngày thường và cuối tuần
        for i in range(1, total_orders + 1):
            order_code = f"ORD-2026-{i:04d}"
            assigned_sales = random.choice(sales_users)
            cust = random.choice(customers)

            # Phân bổ ngày tạo: từ 90 ngày trước tới hôm nay (trung bình 1-2 đơn/ngày)
            days_back = int(random.triangular(0, 90, 30))  # Tập trung nhiều hơn ở 30 ngày gần đây
            order_hour = random.randint(8, 20)
            order_minute = random.randint(0, 59)
            order_date = now_time - timedelta(days=days_back, hours=now_time.hour - order_hour, minutes=now_time.minute - order_minute)

            # Trạng thái: đơn cách đây > 3 ngày phần lớn là completed, đơn mới có pending
            if days_back < 3 and random.random() < 0.4:
                status = "pending"
            else:
                status = "completed"

            order = Order.objects.create(
                customer=cust,
                order_code=order_code,
                payment_method=random.choice(self.PAYMENT_METHODS),
                shipping_provider=random.choice(self.SHIPPING_PROVIDERS),
                status=status,
                assigned_to=assigned_sales,
                notes=random.choice(order_notes_pool),
                total_amount=Decimal("0"),
            )

            # Thêm từ 1 đến 3 sản phẩm cho mỗi đơn hàng
            chosen_products = random.sample(products, k=random.randint(1, 3))
            calculated_total = Decimal("0")
            for prod in chosen_products:
                qty = random.randint(1, 3)
                unit_price = prod.price
                OrderItem.objects.create(
                    order=order,
                    product=prod,
                    quantity=qty,
                    unit_price=unit_price,
                )
                calculated_total += unit_price * Decimal(qty)

            order.total_amount = calculated_total
            order.save(update_fields=["total_amount"])

            # CẬP NHẬT TRỰC TIẾP NGÀY TẠO VÀO CSDL ĐỂ ĐẢM BẢO CHUỖI THỜI GIAN THẬT
            Order.objects.filter(pk=order.pk).update(created_at=order_date)
            created_orders.append(order)

        self.stdout.write(f"   [OK] Đơn hàng: {len(created_orders)} đơn hàng trải dài trong 90 ngày vừa qua")

        # Cập nhật hạng thẻ khách hàng tự động dựa trên tổng chi tiêu
        for c in customers:
            c.update_tier_automatically()

        # ── 6. Tạo Nhật ký tương tác (Interactions) trải đều ────────
        Interaction.objects.all().delete()
        interaction_summaries = [
            ("call", "Gọi điện giới thiệu bản cập nhật phần mềm", "Khách hàng lắng nghe tích cực, quan tâm tính năng tự động đối soát."),
            ("meeting", "Hẹn gặp trực tiếp tại văn phòng khách hàng", "Đã thuyết trình giải pháp CRM Cloud và giải đáp thắc mắc về bảo mật."),
            ("email", "Gửi bảng báo giá chi tiết và hồ sơ năng lực", "Gửi email báo giá kèm chính sách chiết khấu 8% nếu ký hợp đồng trong quý."),
            ("call", "Liên hệ khảo sát mức độ hài lòng sau mua", "Khách hàng rất hài lòng về máy Xprinter, đề xuất mua thêm cho chi nhánh."),
            ("note", "Ghi chú nội bộ: Khách chuẩn bị mở rộng chi nhánh", "Kế hoạch mở thêm cơ sở tại Bình Dương, cần chủ động liên hệ trước."),
            ("call", "Hỏi thăm và nhắc gia hạn gói phần mềm", "Khách hàng xác nhận sẽ gia hạn gói Enterprise thêm 1 năm vào tuần tới."),
            ("meeting", "Demo tính năng AI Insights cho ban giám đốc", "Buổi demo thành công tốt đẹp, giám đốc đánh giá cao khả năng dự báo."),
            ("email", "Gửi tài liệu hướng dẫn sử dụng máy POS Sunmi", "Đã đính kèm video clip và tài liệu PDF cho trưởng ca bán lẻ."),
        ]

        for i in range(45):
            itype, title, content = random.choice(interaction_summaries)
            cust = random.choice(customers)
            user = cust.assigned_to or random.choice(sales_users)
            days_ago = random.randint(1, 85)
            follow_up = (now_time + timedelta(days=random.randint(3, 14))).date() if random.random() > 0.5 else None
            inter_obj = Interaction.objects.create(
                customer=cust,
                user=user,
                interaction_type=itype,
                summary=title,
                content=content,
                follow_up_date=follow_up,
            )
            Interaction.objects.filter(pk=inter_obj.pk).update(interaction_date=now_time - timedelta(days=days_ago))

        self.stdout.write("   [OK] Nhật ký chăm sóc (Interactions): 45 hoạt động tương tác đa dạng")

        # ── 7. Tạo Phiếu hỗ trợ khách hàng (Support Tickets) ────────
        SupportTicket.objects.all().delete()
        ticket_samples = [
            ("Lỗi không kết nối được máy in hóa đơn qua mạng LAN", "Máy in thỉnh thoảng báo Offline, cần kỹ thuật viên hỗ trợ kiểm tra lại IP tĩnh.", "high", "in_progress"),
            ("Yêu cầu cấp lại thông tin đăng nhập tài khoản quản trị", "Admin quên mật khẩu đăng nhập cổng portal, cần reset về email công ty.", "medium", "resolved"),
            ("Thắc mắc về quy trình tích điểm thẻ thành viên VIP", "Khách hỏi điểm thưởng có áp dụng đồng thời với mã giảm giá ngày lễ không.", "low", "closed"),
            ("Máy POS Sunmi không nhận sạc pin", "Cắm nguồn đèn sạc không báo sáng, nghi hỏng củ sạc hoặc chân cắm nguồn.", "urgent", "open"),
            ("Đề nghị xuất hóa đơn điện tử cho đơn hàng tuần trước", "Công ty cần bổ sung hóa đơn GTGT để làm thủ tục hoàn ứng tháng.", "medium", "resolved"),
            ("Hướng dẫn đồng bộ dữ liệu khách hàng từ file Excel", "Doanh nghiệp có 2000 liên hệ cũ muốn import hàng loạt vào hệ thống CRM.", "low", "in_progress"),
            ("Đổi trả máy quét mã vạch bị trầy xước khi vận chuyển", "Hộp hàng bị móp méo trong quá trình chuyển phát nhanh SPX Express.", "high", "pending"),
            ("Tư vấn nâng cấp gói CRM Enterprise cho 50 nhân viên", "Khách hàng muốn tìm hiểu bảng giá ưu đãi khi thanh toán 2 năm liên tiếp.", "medium", "resolved"),
        ]

        for idx, (subject, desc, priority, status) in enumerate(ticket_samples * 3, 1):
            cust = random.choice(customers)
            related_order = random.choice(created_orders) if random.random() > 0.3 else None
            days_ago = random.randint(1, 80)
            ticket_date = now_time - timedelta(days=days_ago)
            resolved_time = ticket_date + timedelta(days=random.randint(1, 4)) if status in ["resolved", "closed"] else None

            t = SupportTicket.objects.create(
                ticket_code=f"TCK-2026-{idx:04d}",
                customer=cust,
                order=related_order,
                subject=subject,
                description=desc,
                priority=priority,
                status=status,
                assigned_to=random.choice(sales_users),
                resolved_at=resolved_time,
            )
            SupportTicket.objects.filter(pk=t.pk).update(created_at=ticket_date)

        self.stdout.write(f"   [OK] Phiếu hỗ trợ (Tickets): {len(ticket_samples) * 3} phiếu CSKH trải dài 80 ngày")

        # ── 8. Kích hoạt Huấn luyện Mô hình AI ngay lập tức ──────────
        self.stdout.write(self.style.MIGRATE_HEADING("\n>> Đang tự động huấn luyện lại 2 mô hình Machine Learning..."))
        ai_res = run_all_ai_pipeline()

        if ai_res.get("success"):
            f_info = ai_res.get("forecasting", {})
            s_info = ai_res.get("segmentation", {})
            self.stdout.write(self.style.SUCCESS("   ✅ Huấn luyện mô hình AI thành công xuất sắc!"))
            self.stdout.write(f"   📈 Mô hình Dự báo Doanh thu ({f_info.get('model_name')}):")
            self.stdout.write(f"      - MAE (Sai số TB)  : {f_info.get('mae'):,.2f} VNĐ (Hợp lý, thực tế)")
            self.stdout.write(f"      - R² Score         : {f_info.get('r2_score')} (Độ chính xác cao)")
            self.stdout.write(f"      - Dự báo tương lai : {f_info.get('days_predicted')} ngày ({f_info.get('from_date')} -> {f_info.get('to_date')})")
            self.stdout.write(f"      - Tổng dự báo      : {f_info.get('total_predicted_revenue'):,.0f} VNĐ")
            self.stdout.write(f"      - Xu hướng         : {f_info.get('trend_note')}")
            self.stdout.write(f"\n   👥 Mô hình Phân khúc Khách hàng ({s_info.get('clusters_count')} Cụm K-Means & RFM):")
            for seg, count in s_info.get("distribution", {}).items():
                self.stdout.write(f"      - {seg}: {count} khách hàng")
        else:
            self.stdout.write(self.style.WARNING("   ⚠️ Huấn luyện AI có lưu ý, vui lòng kiểm tra lại."))

        self.stdout.write(self.style.SUCCESS("\n🎉 TOÀN BỘ QUÁ TRÌNH TẠO DỮ LIỆU ĐA DẠNG & HUẤN LUYỆN AI ĐÃ HOÀN TẤT!"))
