import os
import random
from dataclasses import dataclass
from typing import List


@dataclass
class CommentConfig:
    comment_times: int
    comments: List[str]
    min_delay: float = 2.0
    max_delay: float = 5.0

    @classmethod
    def from_env(cls) -> "CommentConfig":
        comment_times = os.getenv("COMMENT_TIMES")
        if not comment_times:
            raise ValueError("COMMENT_TIMES không được để trống")

        comments_raw = os.getenv("COMMENTS", "")
        comments = [item.strip() for item in comments_raw.split("|") if item.strip()]

        min_delay = float(os.getenv("COMMENT_DELAY_MIN", "2"))
        max_delay = float(os.getenv("COMMENT_DELAY_MAX", "5"))
        if min_delay > max_delay:
            min_delay, max_delay = max_delay, min_delay

        return cls(
            comment_times=int(comment_times),
            comments=comments,
            min_delay=min_delay,
            max_delay=max_delay,
        )

    def pick_comment(self) -> str:
        if not self.comments:
            return "Nice post!"
        return random.choice(self.comments)

