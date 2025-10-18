from random import random
from time import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from config import THREADS_LOGIN_URL, create_driver
import os
from dotenv import load_dotenv
load_dotenv()
# Bộ nhớ cache driver để tái sử dụng giữa các lần gọi
_driver_cache = None
_driver_instance = None


def _create_driver():
    """Tạo mới một undetected Chrome driver dựa trên cấu hình mặc định."""
    return create_driver()


def get_cached_driver():
    """Tái sử dụng driver instance để giảm thời gian khởi động."""
    global _driver_cache
    if _driver_cache is None:
        _driver_cache = _create_driver()
    return _driver_cache


# Monkey patch quit/__del__ để tránh lỗi OSError khi tái sử dụng
_original_quit = uc.Chrome.quit


def _safe_quit(self):
    try:
        _original_quit(self)
    except Exception:
        pass


uc.Chrome.quit = _safe_quit

_original_del = uc.Chrome.__del__


def _safe_del(self):
    try:
        _original_del(self)
    except Exception:
        pass


uc.Chrome.__del__ = _safe_del


def init_selenium_threads():
    """Mở trình duyệt tới trang đăng nhập Threads bằng driver cache."""
    global _driver_instance
    driver = get_cached_driver()
    _driver_instance = driver

    try:
        driver.get(THREADS_LOGIN_URL)
        print("Đã truy cập trang đăng nhập Threads thành công!")
        return driver
    except Exception as exc:
        print(f"Lỗi khi truy cập Threads: {exc}")
        return None


def cleanup_driver_cache():
    """Đóng driver cache khi không còn sử dụng."""
    global _driver_cache, _driver_instance
    if _driver_cache:
        try:
            _driver_cache.quit()
        except Exception:
            pass
        _driver_cache = None
    _driver_instance = None

def login_threads(driver):
    try:
        driver.get(THREADS_LOGIN_URL)
        
        # Đăng nhập username 
        username = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '[placeholder="Username, phone or email"]'))
        )
        for char in os.getenv("THREADS_USERNAME"):
            username.send_keys(char)
            time.sleep(0.05 + random.uniform(0.05, 0.15))

        # Đăng nhập password
        password = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '[placeholder="Password"]'))
        )
        for char in os.getenv("THREADS_PASSWORD"):
            password.send_keys(char)
            time.sleep(0.05 + random.uniform(0.05, 0.15))

        # Click vào nút đăng nhập
        login_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '[type="submit"]'))
        )
        login_button.click()

        print("Đã truy cập trang đăng nhập Threads thành công!")
        return driver
    except Exception as exc:
        print(f"Lỗi khi truy cập Threads: {exc}")
        return None

def main():
    driver = init_selenium_threads()
    if driver:
        login_threads(driver)

if __name__ == "__main__":
    main()
        

