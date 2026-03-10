"""Service layer for generating and caching profiles."""
from datetime import date
from typing import Optional, Dict, Any
import logging
import time

from . import config
from .db import get_cached_profile, store_profile
from .processor import fetch_user_posts_dataframe, prepare_step2_markdown
from .llm import generate_taste_profile_chat

_CATEGORY_NAMES = {3: "restaurants", 2: "tv", 1: "movies", 8: "books"}

def _derive_profile_from_posts(posts):
    """Generate a basic profile from raw post dicts when the LLM is unavailable."""
    seen = set()
    for post in posts:
        cat = _CATEGORY_NAMES.get(post.get("post_category_id"))
        if cat:
            seen.add(cat)
    if not seen:
        return {"taste_profile": {}}
    return {"taste_profile": {cat: f"User has activity in {cat}." for cat in seen}}


def get_user_taste_profile(
    user_id: int,
    as_of: Optional[date] = None,
    category_map: Optional[Dict[int, str]] = None,
    recent_days: int = 90,
) -> Dict[str, Any]:
    """Return a taste profile for a user, using cache when possible.

    This is the public entry point used by the HTTP API and by
    command-line helpers.  It encapsulates the entire workflow:
    cache lookup, data fetch, markdown preparation, LLM call and save.
    """

    if as_of is None:
        as_of = date.today()

    import time, logging
    start = time.time()
    logging.basicConfig(level=logging.INFO)

    cached = get_cached_profile(user_id, as_of)
    if cached:
        logging.info(f"cache hit for user {user_id} date {as_of} (took {time.time()-start:.3f}s)")
        return cached


    if category_map is None:
        category_map = _CATEGORY_NAMES.copy()

    posts = fetch_user_posts_dataframe([user_id])
    if not posts:
        return {"taste_profile": {}}

    markdown_text = prepare_step2_markdown(posts, category_map, recent_days)
    llm_start = time.time()
    profile = generate_taste_profile_chat(markdown_text, None)
    logging.info(f"LLM call took {time.time()-llm_start:.3f}s")

    if isinstance(profile, dict) and profile.get("error"):
        profile = _derive_profile_from_posts(posts)

    store_profile(user_id, as_of, profile)
    return profile
