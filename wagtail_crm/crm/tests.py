import json
from decimal import Decimal
from io import BytesIO
from unittest.mock import Mock, patch
from urllib.error import HTTPError

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from crm.ai_analysis import AIAnalysisError, build_crm_report, request_ai_analysis
from crm.models import Customer, Order

User = get_user_model()


class CRMReportTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_superuser(
			username="admin",
			email="admin@example.com",
			password="test-password",
		)
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

	@patch("crm.views.request_ai_analysis", return_value="Phân tích mẫu")
	def test_wagtail_report_page_displays_ai_response(self, mocked_analysis):
		self.client.force_login(self.user)
		url = reverse("crm_ai_report")

		response = self.client.get(url)
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "Số liệu tổng quan")

		response = self.client.post(url, {"prompt": "Phân tích đơn hàng"})
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "Phân tích mẫu")
		mocked_analysis.assert_called_once()

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
		self.assertEqual(
			request.full_url,
			"https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
		)
		self.assertEqual(payload["model"], "gemini-3.8-flash")
		self.assertIn('"order_count": 3', payload["messages"][1]["content"])

	@patch.dict("os.environ", {"AI_API_KEY": "test-key"})
	@patch("crm.ai_analysis.urlopen")
	def test_quota_error_has_billing_guidance(self, mocked_urlopen):
		mocked_urlopen.side_effect = HTTPError(
			"https://api.openai.com/v1/chat/completions",
			429,
			"Too Many Requests",
			None,
			BytesIO(
				b'{"error":{"status":"RESOURCE_EXHAUSTED",'
				b'"message":"You exceeded your current quota."}}'
			),
		)

		with self.assertRaises(AIAnalysisError) as context:
			request_ai_analysis({"order_count": 1})

		self.assertIn("HTTP 429", str(context.exception))
		self.assertIn("current quota", str(context.exception))

	@patch.dict("os.environ", {"AI_API_KEY": "test-key"})
	@patch("crm.ai_analysis.urlopen")
	def test_rate_limit_error_suggests_retry(self, mocked_urlopen):
		mocked_urlopen.side_effect = HTTPError(
			"https://api.openai.com/v1/chat/completions",
			429,
			"Too Many Requests",
			None,
			BytesIO(b'{"error":{"code":"rate_limit_exceeded"}}'),
		)

		with self.assertRaises(AIAnalysisError) as context:
			request_ai_analysis({"order_count": 1})

		self.assertIn("HTTP 429", str(context.exception))
