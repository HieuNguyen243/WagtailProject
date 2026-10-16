"""
Middleware bổ sung các header bảo mật và whitelist kết nối tới Apache Superset (cổng 8088).
"""

class SupersetIframeSecurityMiddleware:
    """
    Whitelist Apache Superset (http://localhost:8088 và http://127.0.0.1:8088):
    1. Thiết lập Content-Security-Policy (CSP) frame-src cho phép nhúng iframe từ Superset.
    2. Đặt X-Frame-Options thành SAMEORIGIN.
    3. Hỗ trợ Cross-Origin Resource Sharing (CORS) cho các request liên quan.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.path.startswith("/admin/superset/") or request.path.startswith("/superset/"):
            response["X-Frame-Options"] = "SAMEORIGIN"
            response["Content-Security-Policy"] = (
                "frame-src 'self' http://localhost:8088 http://127.0.0.1:8088 https://localhost:8088; "
                "connect-src 'self' http://localhost:8088 http://127.0.0.1:8088; "
                "img-src 'self' data: blob: http://localhost:8088 http://127.0.0.1:8088;"
            )
            response["Access-Control-Allow-Origin"] = "http://localhost:8088"
            response["Access-Control-Allow-Credentials"] = "true"
        return response
