from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [("crm", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="customer",
            name="company",
            field=models.CharField(blank=True, max_length=255, verbose_name="Công ty"),
        ),
        migrations.AddField(
            model_name="customer",
            name="segment",
            field=models.CharField(choices=[("new", "Khách mới"), ("regular", "Khách thường xuyên"), ("vip", "Khách VIP"), ("risk", "Có nguy cơ rời bỏ")], default="new", max_length=20, verbose_name="Phân khúc"),
        ),
        migrations.AddField(
            model_name="customer",
            name="notes",
            field=models.TextField(blank=True, verbose_name="Ghi chú CRM"),
        ),
        migrations.AddField(
            model_name="customer",
            name="ai_summary",
            field=models.TextField(blank=True, verbose_name="AI Summary"),
        ),
        migrations.AddField(
            model_name="customer",
            name="ai_recommendation",
            field=models.TextField(blank=True, verbose_name="AI Recommendation"),
        ),
        migrations.AddField(
            model_name="customer",
            name="ai_email_subject",
            field=models.CharField(blank=True, max_length=255, verbose_name="AI Email Subject"),
        ),
        migrations.AddField(
            model_name="customer",
            name="ai_email_body",
            field=models.TextField(blank=True, verbose_name="AI Email Body"),
        ),
        migrations.AddField(
            model_name="customer",
            name="ai_last_run_at",
            field=models.DateTimeField(blank=True, null=True, verbose_name="Lần chạy AI gần nhất"),
        ),
        migrations.AddField(
            model_name="customer",
            name="updated_at",
            field=models.DateTimeField(auto_now=True, verbose_name="Cập nhật"),
        ),
        migrations.AddField(
            model_name="order",
            name="description",
            field=models.TextField(blank=True, verbose_name="Mô tả đơn hàng"),
        ),
        migrations.AddField(
            model_name="order",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now, verbose_name="Ngày tạo"),
            preserve_default=False,
        ),
        migrations.CreateModel(
            name="AIAnalysisLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("action_type", models.CharField(choices=[("analysis", "Phân tích khách hàng"), ("email", "Gợi ý phản hồi email"), ("report", "Báo cáo CRM")], max_length=20, verbose_name="Loại thao tác")),
                ("model_name", models.CharField(blank=True, max_length=100, verbose_name="Model AI")),
                ("output_text", models.TextField(blank=True, verbose_name="Kết quả AI")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Thời gian")),
                ("customer", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="ai_logs", to="crm.customer", verbose_name="Khách hàng")),
            ],
            options={
                "verbose_name": "Nhật ký AI",
                "verbose_name_plural": "Nhật ký AI",
                "ordering": ["-created_at"],
            },
        ),
    ]
