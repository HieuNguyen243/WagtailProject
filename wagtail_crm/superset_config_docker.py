# ==============================================================================
# 🌐 CẤU HÌNH CHO PHÉP NHÚNG SUPERSET VÀO WAGTAIL CRM (CỔNG 8000)
# ==============================================================================

# 1. Tắt Talisman để không chặn iframe và không ép X-Frame-Options: SAMEORIGIN
TALISMAN_ENABLED = False

# 2. Cho phép iframe từ mọi nguồn hoặc nguồn Wagtail
HTTP_HEADERS = {"X-Frame-Options": "ALLOWALL"}
OVERRIDE_HTTP_HEADERS = {"X-Frame-Options": "ALLOWALL"}

# 3. Kích hoạt CORS và Whitelist các domain Wagtail
ENABLE_CORS = True
CORS_OPTIONS = {
    "supports_credentials": True,
    "allow_headers": ["*"],
    "resources": ["*"],
    "origins": [
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:8088",
        "http://127.0.0.1:8088",
    ],
}

ALLOWED_EMBEDDED_DOMAINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:8088",
    "http://127.0.0.1:8088",
]

# 4. Feature flag nhúng Superset
FEATURE_FLAGS = {
    "EMBEDDED_SUPERSET": True,
}

# 5. Cho phép cookie cross-site không bị trình duyệt chặn trong iframe
SESSION_COOKIE_SAMESITE = None
SESSION_COOKIE_SECURE = False

# 6. Cho phép xem dashboard công khai (Guest/Public) không bắt login
PUBLIC_ROLE_LIKE = "Gamma"
GUEST_ROLE_NAME = "Public"
