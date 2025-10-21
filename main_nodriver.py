import asyncio
import logging
import random

import nodriver as uc
from dotenv import load_dotenv

from bot import ThreadsCommentBot
from config import CommentConfig
import os

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

THREADS_LOGIN_URL = "https://www.threads.com/login"

async def init_driver():
    browser = await uc.start(headless=False, lang="vi")
    return browser

async def login_threads_nodriver(browser):
    """Đăng nhập Threads bằng Nodriver - nhanh hơn undetected_chromedriver."""
    
    page = await browser.get(THREADS_LOGIN_URL)
    
    await page
    # Đăng nhập username
    username_input = await page.select('input[placeholder*="Username"]')
    username = os.getenv("THREADS_USERNAME")
    if username:
        await username_input.click()
        await asyncio.sleep(0.3)
        for char in username:
            await username_input.send_keys(char)
            await asyncio.sleep(0.15 + 0.1 * random.random())
        logger.info("Đã nhập username")

    # Đăng nhập password
    password_input = await page.select('input[placeholder*="Password"]')
    password = os.getenv("THREADS_PASSWORD")
    if password:
        await password_input.click()
        await asyncio.sleep(0.3)
        for char in password:
            await password_input.send_keys(char)
            await asyncio.sleep(0.15 + 0.1 * random.random())
        logger.info("Đã nhập password")

    # Click login
    login_btn = await page.select('div[class="xwhw2v2 x1xdureb"]')
    await login_btn.click()
    
    logger.info("Đăng nhập thành công!")
    return page

async def scrape_threads(page, config: CommentConfig):
    logger.info("Đang xử lý feed")

    bot = ThreadsCommentBot(page, config)
    await bot.run()
        
async def main():
    try:
        config = CommentConfig.from_env()
    except ValueError as exc:
        logger.error(str(exc))
        return

    browser = await init_driver()
    page = await login_threads_nodriver(browser)
    if page is None:
        logger.error("Không thể đăng nhập Threads")
        browser.stop()
        return

    await scrape_threads(page, config)

    await asyncio.to_thread(input, "Nhấn Enter không kiểm tra nữa...")

    # Đóng browser
    browser.stop()
    logger.info("Browser đã đóng")

if __name__ == "__main__":
    uc.loop().run_until_complete(main())