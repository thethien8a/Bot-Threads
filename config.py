import os
import random
from dataclasses import dataclass
from typing import List


@dataclass
class CommentConfig:
    threads_username: str
    threads_password: str
    comment_times: int
    comments: str
    prompt_engineering: str
    gg_api_key_1: str
    gg_api_key_2: str
    min_delay: float = 2.0
    max_delay: float = 5.0
    
    @classmethod
    def from_env(cls) -> "CommentConfig":
        comment_times = os.getenv("COMMENT_TIMES", None)
        if not comment_times:
            raise ValueError("COMMENT_TIMES không được để trống")

        comments = os.getenv("COMMENTS", None)
        if not comments:
            raise ValueError("COMMENTS không được để trống")
        
        prompt_engineering = os.getenv("PROMPT_ENGINEERING", None)
        if not prompt_engineering:
            raise ValueError("PROMPT_ENGINEERING không được để trống")

        gg_api_key_1 = os.getenv("GG_API_KEY_1", None)
        if not gg_api_key_1:
            raise ValueError("GG_API_KEY_1 không được để trống")
        
        gg_api_key_2 = os.getenv("GG_API_KEY_2", None)
        if not gg_api_key_2:
            raise ValueError("GG_API_KEY_2 không được để trống")

        threads_username = os.getenv("THREADS_USERNAME", None)
        if not threads_username:
            raise ValueError("THREADS_USERNAME không được để trống")
        
        threads_password = os.getenv("THREADS_PASSWORD", None)
        if not threads_password:
            raise ValueError("THREADS_PASSWORD không được để trống")

        min_delay = float(os.getenv("COMMENT_DELAY_MIN", None))
        if not min_delay:
            raise ValueError("COMMENT_DELAY_MIN không được để trống")
        
        max_delay = float(os.getenv("COMMENT_DELAY_MAX", None))
        if not max_delay:
            raise ValueError("COMMENT_DELAY_MAX không được để trống")
        
        return cls(
            threads_username=threads_username,
            threads_password=threads_password,
            comment_times=int(comment_times),
            comments=comments,
            prompt_engineering=prompt_engineering,
            gg_api_key_1=gg_api_key_1,
            gg_api_key_2=gg_api_key_2,
            min_delay=min_delay,
            max_delay=max_delay,
        )

    def pick_comment(self) -> str:
        if not self.comments:
            return "Nice post!"
        return random.choice(self.comments)

