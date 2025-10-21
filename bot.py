import asyncio
import logging
import random
from typing import Any

from config import CommentConfig


logger = logging.getLogger(__name__)


class ThreadsCommentBot:
    def __init__(self, page: Any, config: CommentConfig) -> None:
        self.page = page
        self.config = config
        self.processed_ids = set()
        self.comment_count = 0

    async def prepare(self) -> None:
        await asyncio.sleep(5)

    async def collect_posts(self):
        posts = await self.page.select_all("article") or []
        logger.info("Tìm thấy %d bài trên màn hình hiện tại", len(posts))
        return posts

    async def ensure_comment_box(self, post):
        reply_btn = await post.select('svg[aria-label*="Trả lời"]') or await post.find("Trả lời", best_match=True)
        if not reply_btn:
            return None
        await reply_btn.click()
        textarea = await post.select('textarea')
        if textarea:
            await textarea.focus()
        return textarea

    async def submit_comment(self, textarea, comment_text: str) -> bool:
        await textarea.send_keys(comment_text)
        submit_btn = await self.page.select('button[type="submit"]')
        if not submit_btn:
            return False
        await submit_btn.click()
        await asyncio.sleep(2)
        return True

    async def random_pause(self) -> None:
        await asyncio.sleep(random.uniform(self.config.min_delay, self.config.max_delay))

    async def process_post(self, post) -> None:

        await post.scroll_into_view()

        comment_text = self.config.pick_comment()
        if not comment_text:
            logger.error("Không tìm thấy nội dung comment hợp lệ")
            return
        
        textarea = await self.ensure_comment_box(post)
        if not textarea:
            logger.error("Không mở được khung comment ở bài %d", self.comment_count)
            return
        await self.submit_comment(textarea, comment_text)
        
        await self.prepare()

    async def run(self) -> None:
        await self.prepare()

        while self.comment_count < self.config.comment_times:
            posts = await self.collect_posts()
            
            # Nếu posts không cập nhật thêm mới
            if self.comments_count >= len(posts):
                break
            
            # Nếu
            while self.comments_count < len(posts):
                await self.process_post(posts[self.comments_count])
                self.comments_count += 1

            await self.page.scroll_by(0, 1500)
