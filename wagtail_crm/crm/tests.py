from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from .models import AIAnalysisLog, Customer, Order


class CRMTests(TestCase):
    def setUp(self):
        self.customer = Customer.objects.create(
            name="Nguyễn Văn A",
            email="a@example.com",
            phone="0900000000",
            company="ABC",
        )
        self.order = Order.objects.create(
            customer=self.customer,
            order_code="ORD-TEST-001",
            total_amount=Decimal("5000000"),
            status="completed",
        )

    def test_customer_totals(self):
        self.assertEqual(self.customer.total_spent, Decimal("5000000"))
        self.assertEqual(self.customer.order_count, 1)

    def test_public_customer_pages(self):
        self.assertEqual(self.client.get(reverse("crm_public_customers")).status_code, 200)
        self.assertEqual(self.client.get(reverse("crm_public_customer_detail", args=[self.customer.pk])).status_code, 200)

    @patch("crm.views.analyze_customer")
    def test_analyze_customer(self, mock_analyze):
        from django.utils import timezone
        mock_analyze.return_value = {
            "segment": "vip",
            "summary": "Tóm tắt",
            "recommendation": "Đề xuất",
            "model": "test-model",
            "timestamp": timezone.now(),
        }
        from django.contrib.auth import get_user_model
        user = get_user_model().objects.create_user(username="tester", password="pass")
        self.client.force_login(user)
        response = self.client.post(reverse("crm_admin:analyze", args=[self.customer.pk]))
        self.assertEqual(response.status_code, 302)
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.segment, "vip")
        self.assertEqual(AIAnalysisLog.objects.count(), 1)
