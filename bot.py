import asyncio
import logging
import os
import random
from typing import Any
from google import genai
from config import CommentConfig


logger = logging.getLogger(__name__)


class ThreadsCommentBot:
    def __init__(self, page: Any, config: CommentConfig) -> None:
        self.page = page
        self.config = config
        self.processed_ids = set()
        self._comment_count = 0

        # Khởi tạo 1 lần client Gemini dùng cho toàn bộ vòng đời bot
        api_key_candidates = [self.config.gg_api_key_1, self.config.gg_api_key_2]
        api_key_candidates = [k for k in api_key_candidates if k]

        if not api_key_candidates:
            raise ValueError("Không có Gemini API key hợp lệ trong config (gg_api_key_1, gg_api_key_2).")

        self.api_key = random.choice(api_key_candidates)
        logger.info("Đã chọn 1 Gemini API key cho phiên bot hiện tại.")
        self.client = genai.Client(api_key=self.api_key)

    async def prepare(self) -> None:
        await asyncio.sleep(5)

    async def collect_posts(self):
        posts = await self.page.select_all("div[class='x78zum5 xdt5ytf']") or []
        logger.info("Tìm thấy %d bài trên màn hình hiện tại", len(posts))
        return posts

    async def ensure_comment_box(self, post):
        reply_btn = await post.query_selector('svg[aria-label="Reply"][class="x1lliihq x2lah0s x1n2onr6 x16ye13r x5lhr3w x1i0azm7 xbh8q5q x73je2i x1f6yumg xvlca1e"]')

        if not reply_btn:
            logger.error("Không tìm thấy nút reply")
            return None

        js_click = """
        (elem) => {
            const button = elem.closest('button, div[role="button"], div[tabindex]');
            if (button) {
                button.click();
                return true;
            }
            elem.click();
            return false;
        }
        """

        try:
            used_parent = await reply_btn.apply(js_click)
        except Exception as exc:
            logger.warning("Click SVG trực tiếp do lỗi khi chạy JS: %s", exc)
            used_parent = False

        if not used_parent:
            await reply_btn.click()

        logger.info("Đã click vào nút trả lời cho bài %d", self._comment_count + 1)
        
        await asyncio.sleep(3)
        
        textarea = await post.query_selector('div[aria-label*="Empty text field"]')
        if not textarea:
            logger.error("Không tìm thấy khung comment ở bài %d", self._comment_count+1)
            return None
        
        await textarea.focus()
        logger.info("Đã focus vào khung comment ở bài %d", self._comment_count+1)
        
        return textarea

    async def submit_comment(self, textarea, comment_text: str) -> bool:
        await self.type_like_human(textarea, comment_text)
        submit_btn = await self.page.select('svg[aria-label="Reply"][class="x1lliihq x2lah0s x1n2onr6 x16ye13r x5lhr3w xtlf3c xbh8q5q x73je2i x1owpc8m x1f6yumg xvlca1e"]')
        if not submit_btn:
            return False

        js_click = """
        (elem) => {
            const button = elem.closest('button, div[role="button"], div[tabindex]');
            if (button) {
                button.click();
                return true;
            }
            elem.click();
            return false;
        }
        """

        try:
            used_parent = await submit_btn.apply(js_click)
        except Exception as exc:
            logger.warning("Submit SVG click fallback do lỗi JS: %s", exc)
            used_parent = False

        if not used_parent:
            await submit_btn.click()
        await asyncio.sleep(random.uniform(0.8, 1.5))
        return True

    async def analyze_post(self, post) -> bool:
        await post.scroll_into_view()
        logger.info("Đã scroll vào bài %d", self._comment_count + 1)
        await self.observe_post()

        js_get_content = """
        (postElement) => {
            try {
                const el = postElement.querySelector('div.x1a6qonq.x6ikm8r.x10wlt62.xj0a0fe.x126k92a.x6prxxf.x7r5mf7');
                if (!el) {
                    return null;
                }
                // textContent: chỉ lấy text bên trong, không lấy HTML
                const text = el.textContent || "";
                return text.trim();
            } catch (e) {
                return null;
            }
        }
        """

        try:
            content = await post.apply(js_get_content)
        except Exception as exc:
            logger.error("Lỗi khi thực thi JS lấy nội dung bài viết: %s", exc)
            content = None

        if content:
            logger.info("Nội dung bài viết: %s", content)
        else:
            logger.warning("Không tìm thấy nội dung bài viết hoặc nội dung rỗng")
        
        prompt_engineering = self.config.prompt_engineering
        full_prompt = f"{prompt_engineering}\n\nNội dung: {content}"

        # Gọi Gemini bằng client cố định đã khởi tạo trong __init__
        def call_gemini():
            response = self.client.models.generate_content(
                model="gemini-2.5-flash-lite",
                contents=full_prompt,
            )
            # Đảm bảo luôn trả về string để xử lý an toàn
            return getattr(response, "text", str(response))

        logger.info("Đang gọi Gemini API để phân tích bài viết ...")
        try:
            # Đưa blocking I/O sang thread pool để không chặn event loop 
            response_text = await asyncio.to_thread(call_gemini)
            logger.info("Đã nhận phản hồi từ Gemini")
        except Exception as exc:
            logger.error("Lỗi khi gọi Gemini API: %s", exc)
            return None

        if "True" in response_text:
            return True
        else:
            return None
    
    async def random_pause(self) -> None:
        base_delay = random.uniform(self.config.min_delay, self.config.max_delay)
        jitter = random.uniform(0.8, 2.0)
        await asyncio.sleep(base_delay + jitter)

    async def observe_post(self) -> None:
        dwell_time = random.uniform(1.5, 3.5)
        logger.info("Đang quan sát bài viết trong %.1f giây", dwell_time)
        await asyncio.sleep(dwell_time)

    async def cooldown_after_failure(self) -> None:
        cooldown = random.uniform(6.0, 12.0)
        logger.info("Tạm nghỉ %.1f giây sau khi thất bại", cooldown)
        await asyncio.sleep(cooldown)

    async def type_like_human(self, textarea, comment_text: str) -> None:
        for char in comment_text:
            await textarea.send_keys(char)
            await asyncio.sleep(random.uniform(0.05, 0.15))
        await asyncio.sleep(random.uniform(0.3, 0.6))

    async def process_post(self, post) -> bool:

        comment_text = self.config.pick_comment()
        if not comment_text:
            logger.error("Không tìm thấy nội dung comment hợp lệ")
            return False

        textarea = await self.ensure_comment_box(post)
        if not textarea:
            logger.error("Không mở được khung comment ở bài %d", self._comment_count + 1)
            return False

        submitted = await self.submit_comment(textarea, comment_text)

        if submitted:
            logger.info(
                "Đã comment %d/%d: %s",
                self._comment_count + 1,
                self.config.comment_times,
                comment_text,
            )
            return True

        logger.error("Comment thất bại ở bài %d", self._comment_count + 1)
        return False

    async def run(self) -> None:
        # Chuẩn bị thu thập dữ liệu
        await self.prepare()
        
        while self._comment_count < self.config.comment_times or len(posts) > 100:
            posts = await self.collect_posts()
            
            # Nếu posts không cập nhật thêm mới
            if self._comment_count >= len(posts):
                break
            
            # Nếu posts có cập nhật, ta thu thập tất cả các post mới nhất
            post_attempts = 0
            max_attempts = 3
            while self._comment_count < len(posts) and self._comment_count < self.config.comment_times:
                
                analyze_result = await self.analyze_post(posts[self._comment_count])
                if not analyze_result:
                    logger.error("Bài %d không phù hợp với điều kiện", self._comment_count + 1)
                    self._comment_count += 1
                    continue

                try:
                    result = await self.process_post(posts[self._comment_count])
                except Exception as e:
                    logger.error("Lỗi khi comment bài %d: %s", self._comment_count, e)
                    result = False

                if result:
                    self._comment_count += 1
                    post_attempts = 0
                    await self.random_pause()
                else:
                    post_attempts += 1
                    if post_attempts >= max_attempts:
                        logger.error(
                            "Bỏ qua bài %d sau %d lần thử không thành công",
                            self._comment_count + 1,
                            max_attempts,
                        )
                        self._comment_count += 1
                        post_attempts = 0
                    else:
                        logger.info(
                            "Thử lại bài %d sau lần thất bại thứ %d",
                            self._comment_count + 1,
                            post_attempts,
                        )
                        await self.cooldown_after_failure()

            await self.page.scroll_down(random.randint(1200, 1800))
            await asyncio.sleep(random.uniform(2.0, 3.5))

