"""Utilities for loading and cleaning posts."""
from datetime import datetime, timedelta
import csv
import json
import re
import os
from typing import Dict, List, Any

from .db import USE_DB, get_engine

# Type alias: each post is a plain dict
Post = Dict[str, Any]


def _parse_dt(value) -> datetime | None:
    """Parse a datetime string or datetime object; return None on failure."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(str(value), fmt)
        except ValueError:
            continue
    return None


def _clean_text(text) -> str:
    if not text:
        return "N/A"
    text = str(text)
    text = re.sub(r"#\S+", "", text)
    text = text.replace("\n", " ").replace("\r", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip() or "N/A"


def fetch_user_posts_dataframe(user_ids) -> List[Post]:
    """Return posts for the given user IDs as a list of dicts.

    If ``USE_DB`` is true the data is read directly from the ``user_post``
    table.  Otherwise fall back to a JSON file pointed at by the
    ``POSTS_JSON`` environment variable.  An empty list is returned if no
    source is available or the list of IDs is empty.
    """
    if not user_ids:
        return []

    id_set = {int(uid) for uid in user_ids}

    if USE_DB:
        engine = get_engine()
        ids = ",".join(str(i) for i in id_set)
        query = (
            f"SELECT user_id, post_category_id, msg, location_name, latitude,"
            f" longitude, rating, created_on FROM user_post"
            f" WHERE user_id IN ({ids})"
        )
        try:
            with engine.connect() as conn:
                from sqlalchemy import text
                rows = conn.execute(text(query)).mappings().all()
                return [dict(r) for r in rows]
        except Exception:
            return []

    posts_json = os.environ.get("POSTS_JSON")
    if posts_json and os.path.exists(posts_json):
        with open(posts_json) as f:
            all_posts = json.load(f)
        return [p for p in all_posts if int(p.get("user_id", -1)) in id_set]

    return []


def prepare_step2_markdown(posts: List[Post], category_map: Dict[int, str], recent_days: int = 90) -> str:
    """Convert raw posts to the markdown fragment used by the LLM."""
    if not posts:
        return ""

    cutoff = datetime.now() - timedelta(days=recent_days)

    # Enrich each post in place
    enriched = []
    for p in posts:
        cat = category_map.get(p.get("post_category_id"))
        if cat is None:
            continue
        dt = _parse_dt(p.get("created_on"))
        enriched.append({
            **p,
            "msg": _clean_text(p.get("msg")),
            "category": cat,
            "_dt": dt,
            "period": "LONG_TERM" if (dt and dt < cutoff) else "RECENT",
        })

    if not enriched:
        return ""

    # Group: user_id -> period -> category -> [posts]
    users: Dict[int, Any] = {}
    for p in enriched:
        uid = p["user_id"]
        users.setdefault(uid, {"LONG_TERM": {}, "RECENT": {}})
        users[uid][p["period"]].setdefault(p["category"], []).append(p)

    markdown_output = ""
    for user_id, periods in users.items():
        markdown_output += f"\n## USER: {user_id}\n\n"
        for period in ("LONG_TERM", "RECENT"):
            cats = periods[period]
            if not cats:
                continue
            markdown_output += f"### {period.replace('_', ' ').title()}\n\n"
            for category, cat_posts in cats.items():
                markdown_output += f"*Category: {category.capitalize()}*\n\n"
                for row in cat_posts:
                    location = row.get("location_name") or "N/A"
                    rating = row.get("rating") or "N/A"
                    date_str = row["_dt"].strftime("%Y-%m-%d") if row["_dt"] else "N/A"
                    markdown_output += f"- {row['msg']} | Rating: {rating} | Location: {location} | Date: {date_str}\n"
                markdown_output += "\n"

    return markdown_output
