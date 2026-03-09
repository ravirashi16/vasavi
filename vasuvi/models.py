"""Pydantic models describing the structure of a taste profile."""

from typing import Optional, Dict

from pydantic import BaseModel


class TasteProfile(BaseModel):
    restaurants: Optional[str] = None
    movies: Optional[str] = None
    tv: Optional[str] = None
    books: Optional[str] = None


class UserProfile(BaseModel):
    taste_profile: Dict[str, str]
