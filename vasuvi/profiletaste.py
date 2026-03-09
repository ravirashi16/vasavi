# legacy entrypoint retained for compatibility
# the functionality has been spread across multiple modules for better
# maintainability; new code should import directly from those modules.

from .processor import fetch_user_posts_dataframe, prepare_step2_markdown
from .llm import generate_taste_profile_chat
from .core import get_user_taste_profile
from .db import get_cached_profile, store_profile, get_engine

__all__ = [
    "fetch_user_posts_dataframe",
    "prepare_step2_markdown",
    "generate_taste_profile_chat",
    "get_user_taste_profile",
    "get_cached_profile",
    "store_profile",
    "get_engine",
]
