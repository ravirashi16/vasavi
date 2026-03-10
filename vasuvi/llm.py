"""LLM utilities."""

import re
import json

import anthropic
import os

from . import config
from .models import UserProfile


def generate_taste_profile_chat(markdown_text: str, api_key: str) -> dict:
    """Return a structured taste profile from Claude."""
    if api_key is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if api_key is None:
            # missing key; return error instead of raising so caller can fall back
            return {"error": "Anthropic API key not set"}
    client = anthropic.Anthropic(api_key=api_key)

    prompt = f"""
You are generating a structured behavioral taste profile.

Analyze the Markdown input and identify:
1. Long-term preferences (historical patterns)
2. Recent shifts or explorations
3. Clear contrast between them

STRICT RULES:
- Do NOT list specific venue names.
- Abstract patterns (cuisine type, genre, style, ambiance).
- Contrast long-term vs recent explicitly.
- Use this format:
    "User prefers X long-term. Recently, they have been exploring Y."
- Maximum 2 sentences per category.
- No filler language.
- No commentary.
- If no data exists for a category, OMIT the category completely.
- Return ONLY valid JSON.
- Do NOT wrap JSON in quotes.
- Do NOT escape JSON.
- Do NOT use markdown formatting.

### Structured Output
Please produce a single JSON object that matches the schema shown below.

```json
{{ "taste_profile": {{ "restaurants": "...", "movies": "...", "tv": "...", "books": "..." }} }}
```

Markdown Input:
{markdown_text}

Return JSON in this structure (only include categories with data):

{{
  "taste_profile": {{
    "restaurants": "...",
    "movies": "...",
    "tv": "...",
    "books": "..."
  }}
}}
"""

    try:
        message = client.messages.create(
            model=config.ANTHROPIC_MODEL,
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}],
        )
    except Exception as e:
        return {"error": f"API call failed: {str(e)}"}

    content_list = getattr(message, "content", [])
    if content_list and hasattr(content_list[0], "text"):
        llm_output = content_list[0].text.strip()
    else:
        llm_output = str(message).strip()

    llm_output = re.sub(r"⁠  json|  ⁠", "", llm_output).strip()

    try:
        parsed = json.loads(llm_output)
        if isinstance(parsed.get("taste_profile"), str):
            try:
                parsed["taste_profile"] = json.loads(parsed["taste_profile"])
            except json.JSONDecodeError:
                pass

        validated = UserProfile(**parsed)
        cleaned_profile = {
            k: v for k, v in validated.taste_profile.items()
            if v and isinstance(v, str) and v.strip() != ""
        }
        return {"taste_profile": cleaned_profile}

    except Exception as e:
        return {
            "error": "Invalid JSON returned by model",
            "details": str(e),
            "raw_output": llm_output,
        }
