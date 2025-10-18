import undetected_chromedriver as uc

THREADS_LOGIN_URL = "https://www.threads.com/login"

# Danh sách các flag cấu hình Chrome nhằm tối ưu tốc độ khởi động và giảm khả năng bị phát hiện
CHROME_ARGUMENTS = [
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-blink-features=AutomationControlled",
    "--disable-extensions",
    "--disable-plugins",
    "--disable-gpu",
    "--disable-software-rasterizer",
    "--disable-web-security",
    "--disable-features=VizDisplayCompositor",
    "--log-level=3",
    "--no-default-browser-check",
    "--no-first-run",
    "--disable-notifications",
    "--disable-popup-blocking",
    "--disable-background-networking",
    "--password-store=basic",
    "--metrics-recording-only",
    "--disable-client-side-phishing-detection",
    "--disable-component-update",
    "--disable-features=Translate,BackForwardCache,AutofillServerCommunication",
    "--blink-settings=imagesEnabled=false",
    "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

EXPERIMENTAL_PREFS = {
    "profile.default_content_setting_values.notifications": 2,
    "profile.default_content_setting_values.images": 2,
    "credentials_enable_service": False,
    "profile.password_manager_enabled": False,
}


def build_chrome_options() -> uc.ChromeOptions:
    options = uc.ChromeOptions()
    for arg in CHROME_ARGUMENTS:
        options.add_argument(arg)
    options.page_load_strategy = "eager"
    options.add_experimental_option("prefs", EXPERIMENTAL_PREFS)
    return options


def create_driver() -> uc.Chrome:
    """Khởi tạo và trả về một undetected Chrome driver với cấu hình mặc định."""
    print("Khởi tạo Chrome driver mới...")
    options = build_chrome_options()
    driver = uc.Chrome(options=options)
    print("Driver đã sẵn sàng!")
    return driver
