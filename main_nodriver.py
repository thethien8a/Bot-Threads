import asyncio
import os
import nodriver as uc
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

THREADS_LOGIN_URL = "https://www.threads.com/login"

async def init_driver():
    browser = await uc.start(headless=False)
    return browser

async def login_threads_nodriver(browser):
    """Đăng nhập Threads bằng Nodriver - nhanh hơn undetected_chromedriver."""

    page = await browser.get(THREADS_LOGIN_URL)
    
    # Đăng nhập username
    username_input = await page.select('input[placeholder*="Username"]')
    username = os.getenv("THREADS_USERNAME")
    if username:
        await username_input.send_keys(username)
        logger.info("Đã nhập username")

    # Đăng nhập password
    password_input = await page.select('input[placeholder*="Password"]')
    password = os.getenv("THREADS_PASSWORD")
    if password:
        await password_input.send_keys(password)
        logger.info("Đã nhập password")

    # Click login
    login_btn = await page.select('div[class="xwhw2v2 x1xdureb"]')
    await login_btn.click()

    # Chờ điều hướng hoàn tất và trả về tab hiện tại
    await wait_for_home(page)

    logger.info("Đăng nhập thành công!")
    return page

async def wait_for_home(page, timeout=15):
    try:
        await page.wait_for_selector('div[role="feed"]', timeout=timeout * 1000)
    except Exception as exc:
        logger.warning("Không tìm thấy feed sau khi đăng nhập: %s", exc)
        await asyncio.sleep(timeout)

async def scrape_threads(page, comment_times=10):
    logger.info("Đang xử lý feed")

    count = 0
    while count < comment_times:
        # Tìm tất cả bài đăng hiện tại
        posts = await page.select_all('div[class="x78zum5 xdt5ytf"]')
        logger.info(f"Số bài đăng hiện tại: {len(posts)}")
        
        # Thả comment cho từng bài đăng
        logger.info(f"Đang thả comment cho bài đăng {count + 1} / {comment_times}")
        try:
            post = posts[count]
        except Exception as e:
            logger.error(f"Lỗi khi thả comment: {e}")
        
        # Kéo màn hình đến bài đăng tương ứng
        await post.scroll_into_view()
        
        count += 1
    
async def main():
    # Xác định số bài đăng cần thả comment
    comment_times = os.getenv("COMMENT_TIMES")
    if not comment_times:
        logger.error("COMMENT_TIMES không được để trống")
        return

    browser = await init_driver()
    page = await login_threads_nodriver(browser)
    if page is None:
        logger.error("Không thể đăng nhập Threads")
        browser.stop()
        return

    await scrape_threads(page, int(comment_times))

    await asyncio.to_thread(input, "Nhấn Enter không kiểm tra nữa...")

    # Đóng browser
    browser.stop()
    logger.info("Browser đã đóng")

if __name__ == "__main__":
    uc.loop().run_until_complete(main())