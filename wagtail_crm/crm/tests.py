import json
from decimal import Decimal
from unittest.mock import Mock, patch

from django.test import TestCase

from crm.ai_analysis import build_crm_report, request_ai_analysis
from crm.models import Customer, Order


class CRMReportTests(TestCase):
	def setUp(self):
		self.customer = Customer.objects.create(
			name="Test Customer",
			email="test@example.com",
		)
		Order.objects.create(
			customer=self.customer,
			order_code="TEST-001",
			total_amount=Decimal("125000.00"),
			status="completed",
		)

	def test_report_contains_aggregates_without_customer_details(self):
		report = build_crm_report()

		self.assertEqual(report["customer_count"], 1)
		self.assertEqual(report["order_count"], 1)
		self.assertEqual(Decimal(report["total_revenue_vnd"]), Decimal("125000.00"))
		self.assertEqual(report["orders_by_status"], {"Hoàn thành": 1})
		self.assertNotIn("test@example.com", json.dumps(report))
		self.assertNotIn("Test Customer", json.dumps(report))

	@patch.dict("os.environ", {"AI_API_KEY": "test-key"})
	@patch("crm.ai_analysis.urlopen")
	def test_analysis_sends_report_and_returns_response(self, mocked_urlopen):
		response = Mock()
		response.read.return_value = json.dumps(
			{"choices": [{"message": {"content": "Phân tích mẫu"}}]}
		).encode("utf-8")
		mocked_urlopen.return_value.__enter__.return_value = response

		result = request_ai_analysis({"order_count": 3}, "Phân tích đơn hàng")

		request = mocked_urlopen.call_args.args[0]
		payload = json.loads(request.data.decode("utf-8"))
		self.assertEqual(result, "Phân tích mẫu")
		self.assertEqual(request.get_header("Authorization"), "Bearer test-key")
		self.assertIn('"order_count": 3', payload["messages"][1]["content"])
