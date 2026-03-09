"""Utilities for loading and cleaning posts."""
from datetime import datetime, timedelta
import re
from typing import Dict

import pandas as pd
import os

from .db import USE_DB, get_engine


def fetch_user_posts_dataframe(user_ids):
    """Return posts for the given user IDs as a DataFrame.

    If ``USE_DB`` is true the data is read directly from the ``user_post``
    table.  Otherwise fall back to loading a CSV/JSON file pointed at by the
    ``POSTS_CSV``/``POSTS_JSON`` environment variables.  An empty frame is
    returned if no source is available or the list of IDs is empty.
    """
    if not user_ids:
        return pd.DataFrame()

    if USE_DB:
        engine = get_engine()
        ids = ",".join(str(int(uid)) for uid in user_ids)
        query = (
            "SELECT user_id, post_category_id, msg, location_name, latitude, \
"
            "longitude, rating, created_on FROM user_post"
            f" WHERE user_id IN ({ids})"
        )
        try:
            return pd.read_sql(query, engine)
        except Exception:
            # on failure return empty frame rather than falling back to files
            return pd.DataFrame()

    posts_csv = os.environ.get("POSTS_CSV")
    if posts_csv and os.path.exists(posts_csv):
        return pd.read_csv(posts_csv)

    posts_json = os.environ.get("POSTS_JSON")
    if posts_json and os.path.exists(posts_json):
        return pd.read_json(posts_json)

    return pd.DataFrame()


def prepare_step2_markdown(df, category_map, recent_days=90):
    """Convert raw posts to the markdown fragment used by the LLM.

    This function is largely unchanged from the original script, but lives
    in its own module to keep concerns separated.
    """
    df = df.copy()

    def clean_text(text):
        if pd.isnull(text):
            return "N/A"
        text = str(text)
        text = re.sub(r"#\S+", "", text)
        text = text.replace("\n", " ").replace("\r", " ")
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    df["msg"] = df["msg"].apply(clean_text)
    df["created_on"] = pd.to_datetime(
        df["created_on"], errors="coerce"
    )
    df["category"] = df["post_category_id"].map(category_map)

    df["category"] = df["category"].apply(lambda x: str(x) if pd.notnull(x) else x)
    df = df[df["category"].notnull()]

    cutoff = datetime.now() - timedelta(days=recent_days)
    df["period"] = df["created_on"].apply(
        lambda x: "LONG_TERM" if pd.notnull(x) and x < cutoff else "RECENT"
    )

    markdown_output = ""
    for user_id in df["user_id"].unique():
        markdown_output += f"\n## USER: {user_id}\n\n"
        user_df = df[df["user_id"] == user_id]

        for period in ["LONG_TERM", "RECENT"]:
            period_df = user_df[user_df["period"] == period]
            if period_df.empty:
                continue

            markdown_output += f"### {period.replace('_',' ').title()}\n\n"

            for category in period_df["category"].unique():
                cat_df = period_df[period_df["category"] == category]

                markdown_output += f"*Category: {category.capitalize()}*\n\n"

                for _, row in cat_df.iterrows():
                    location = row["location_name"] if row["location_name"] else "N/A"
                    rating = row["rating"] if row["rating"] else "N/A"
                    date_str = row["created_on"].strftime("%Y-%m-%d") if pd.notnull(row["created_on"]) else "N/A"

                    markdown_output += f"- {row['msg']} | Rating: {rating} | Location: {location} | Date: {date_str}\n"

                markdown_output += "\n"

    return markdown_output
