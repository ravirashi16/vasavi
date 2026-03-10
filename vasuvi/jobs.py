"""Batch and scheduled utilities for the taste profile service."""
from datetime import date
from typing import List

from .db import get_engine
from .core import get_user_taste_profile
import pandas as pd
import logging

# simple job to refresh profiles for users who have new posts since the last
# profile generation.  This can be invoked periodically (e.g. via cron) or
# integrated into a background scheduler.

def users_needing_refresh() -> List[int]:
    """Return list of user_ids whose posts are newer than their latest profile."""
    engine = get_engine()
    sql = """
    SELECT DISTINCT up.user_id
    FROM user_post up
    LEFT JOIN taste_profiles tp ON tp.user_id = up.user_id
    WHERE tp.profile_date IS NULL OR up.created_on > tp.profile_date
    """
    df = pd.read_sql(sql, engine)
    return df['user_id'].tolist()


def refresh_profiles_for_active_users(as_of: date = None):
    """Generate or update profiles for all users with recent activity."""
    if as_of is None:
        as_of = date.today()
    ids = users_needing_refresh()
    logging.info(f"refreshing profiles for {len(ids)} users")
    for uid in ids:
        try:
            profile = get_user_taste_profile(uid, as_of=as_of)
            logging.info(f"generated profile for user {uid}")
        except Exception as exc:
            logging.exception(f"failed to refresh user {uid}: {exc}")
