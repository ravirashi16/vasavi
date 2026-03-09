from datetime import datetime, date
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from vasuvi import get_user_taste_profile

app = FastAPI(
    title="Taste Profile Service",
    description="Simple REST API to fetch or compute a user's taste profile.",
    version="0.1.0",
)


class ProfileResponse(BaseModel):
    taste_profile: dict


@app.get("/health", summary="Health check")
async def health():
    return {"status": "ok", "time": datetime.utcnow().isoformat()}


@app.get(
    "/users/{user_id}/profile",
    response_model=ProfileResponse,
    summary="Get a user's taste profile",
)
async def get_profile(
    user_id: int,
    date_str: Optional[str] = Query(
        None,
        description="Optional ISO date (YYYY-MM-DD) of the profile. Defaults to today.",
    ),
):
    """Fetch or compute a user's taste profile.  Date defaults to today."""

    if date_str:
        try:
            as_of = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="date must be YYYY-MM-DD")
    else:
        as_of = None

    try:
        profile = get_user_taste_profile(user_id, as_of=as_of)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return profile


