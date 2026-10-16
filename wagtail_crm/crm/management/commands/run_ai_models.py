# crm/management/commands/run_ai_models.py
"""
Django Management Command: python manage.py run_ai_models
Kích hoạt toàn bộ pipeline AI:
1. Huấn luyện mô hình chuỗi thời gian Ridge Regression để dự báo doanh thu 7 ngày (1 tuần) tiếp theo.
2. Phân khúc khách hàng tự động theo chuẩn RFM + K-Means Clustering và dự đoán rủi ro rời bỏ (Churn Risk).
3. Lưu toàn bộ kết quả vào CSDL bảng RevenueForecast và CustomerSegment phục vụ trực quan hóa trên Apache Superset / Wagtail.
"""

import sys
from django.core.management.base import BaseCommand
from crm.ai_engine import run_revenue_forecasting, run_customer_segmentation

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


class Command(BaseCommand):
    help = "Chạy toàn bộ pipeline Machine Learning (Dự báo doanh thu & Phân khúc RFM K-Means)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=7,
            help="Số ngày tương lai cần dự báo doanh thu (mặc định: 7 ngày / 1 tuần)",
        )
        parser.add_argument(
            "--clusters",
            type=int,
            default=4,
            help="Số lượng cụm K-Means phân khúc khách hàng (mặc định: 4 cụm)",
        )

    def handle(self, *args, **options):
        days = options.get("days", 7)
        clusters = options.get("clusters", 4)

        self.stdout.write(self.style.NOTICE("=================================================="))
        self.stdout.write(self.style.NOTICE("   WAGTAIL CRM - MACHINE LEARNING PIPELINE ENGINE"))
        self.stdout.write(self.style.NOTICE("=================================================="))

        # 1. Dự báo doanh thu
        self.stdout.write("\n[1/2] Dang chay mo hinh Time-Series Revenue Forecasting...")
        forecast_res = run_revenue_forecasting(days_ahead=days)
        if forecast_res.get("success"):
            self.stdout.write(
                self.style.SUCCESS(
                    f"[OK] Du bao thanh cong {forecast_res['days_predicted']} ngay tiep theo ({forecast_res['from_date']} -> {forecast_res['to_date']})"
                )
            )
            self.stdout.write(f"     - Mo hinh: {forecast_res['model_name']}")
            self.stdout.write(f"     - Tong doanh thu du kien: {forecast_res['total_predicted_revenue']:,.0f} VND")
            self.stdout.write(f"     - Chi so danh gia: MAE = {forecast_res['mae']:,.2f} | R2 Score = {forecast_res['r2_score']}")
            self.stdout.write(f"     - Nhan xet xu huong: {forecast_res['trend_note']}")
        else:
            self.stdout.write(self.style.ERROR(f"[FAIL] Loi du bao: {forecast_res.get('error')}"))

        # 2. Phân khúc khách hàng
        self.stdout.write("\n[2/2] Dang chay mo hinh Customer RFM & K-Means Clustering...")
        seg_res = run_customer_segmentation(n_clusters=clusters)
        if seg_res.get("success"):
            self.stdout.write(
                self.style.SUCCESS(
                    f"[OK] Phan khuc thanh cong {seg_res['total_customers']} khach hang thanh {seg_res['clusters_count']} cum K-Means"
                )
            )
            self.stdout.write("     - Co cau phan khuc:")
            for seg_name, count in seg_res["distribution"].items():
                self.stdout.write(f"       * {seg_name}: {count} khach hang")
            self.stdout.write("     - Co cau rui ro roi bo (Churn Risk):")
            for risk_level, count in seg_res["churn_distribution"].items():
                self.stdout.write(f"       * Muc {risk_level.upper()}: {count} khach hang")
        else:
            self.stdout.write(self.style.ERROR(f"[FAIL] Loi phan khuc: {seg_res.get('error')}"))

        self.stdout.write(self.style.NOTICE("\n=================================================="))
        self.stdout.write(
            self.style.SUCCESS(
                "[HOAN TAT] Ket qua AI da luu vao CSDL (bang RevenueForecast va CustomerSegment)!"
            )
        )
        self.stdout.write(self.style.NOTICE("Apache Superset va Wagtail Dashboard da co the doc truc tiep."))
        self.stdout.write(self.style.NOTICE("=================================================="))
