# Taste Profile Service (vasuvi)

This repository contains a small library and HTTP API for generating and
caching a user's "taste profile" based on posts they've made in the Recz
application.  The original algorithm was implemented in a one‑off script
(`profiletaste.py`); the goal of this project is to turn it into a deployable
service that can scale and avoids calling Claude on every request.

> **Note:** the database backend has been removed entirely for local
> development.  All caching now happens in a simple **JSON file**; the rest of
> the codebase still uses the same API, but no network connections are
> required.  You can control the cache path with the `DB_JSON_PATH`
> environment variable (default: `taste_profiles.json`).

To simulate user posts when no real database exists, create a JSON file and
set the `POSTS_JSON` environment variable to its path.  A sample file with
realistic entries is included as `sample_posts.json` in this repo.

> **Tip:** if `POSTS_JSON` (or `POSTS_CSV`) is not defined the library will
> behave as if the user has no posts, and `get_user_taste_profile` will
> immediately return `{ "taste_profile": {} }`.  This often looks like the
> API "not giving a result" when the service is started without pointing at
> any data.  For offline testing you can still call the endpoint without a
> Claude key; the code will fall back to a very basic profile derived from
> whatever posts are available.

The service also supports reading live data from a MySQL database.  Set
`USE_DB=1` in the environment and ensure your database credentials are
provided (`DB_USER`, `DB_PASSWORD`, etc.).  When the flag is enabled all
post lookups (`user_post` table) and cache operations hit the database; the
JSON/CSV paths are ignored entirely.  This mirrors production behaviour and
enables you to switch between file‑based testing and a real backend simply
by toggling the environment variable.

If you have an existing Excel export of posts (e.g. `User_ID_profile.xlsx`),
you can convert it using the helper script:

```bash
python tools/convert_excel.py User_ID_profile.xlsx sample_posts.json
```

This will overwrite `sample_posts.json` with the 491 rows from the sheet.
Feel free to modify or trim the generated data for testing.


The code has since been refactored into several focused modules –
`processor`, `llm`, `db`, `models` and `core` – to improve maintainability
and make individual pieces easier to test or replace.  The old
`profiletaste.py` file exists only as a lightweight compatibility shim.

---

## Overview

1. **Input**  – a `user_id` (integer) and an optional date.  If no date is
   supplied the server assumes *today*.
2. **Cache lookup** – profiles are stored in a MySQL table called
   `taste_profiles` keyed by `(user_id, profile_date)`.  The first time a
   user/date is requested we fall through to step 3.
3. **Profile generation** – we fetch the user's posts from the `user_post`
   table, clean and format them into Markdown, then send that text to Claude
   using the Anthropic Python SDK.  The LLM returns a JSON blob that is
   validated with pydantic.
4. **Store & return** – the freshly generated profile is persisted and then
   returned to the caller.

**Example schema** for `taste_profiles` (see code in
[`vasuvi/db.py`](vasuvi/db.py)):

| Column        | Type        | Notes                                      |
|---------------|-------------|--------------------------------------------|
| user_id       | BIGINT      | part of primary key                        |
| profile_date  | DATE        | part of primary key (usually today)        |
| payload       | JSON        | taste profile structure returned by LLM    |
| created_on    | DATETIME    | when the row was inserted/updated         |

Because generation is expensive (Claude calls cost tokens) we avoid
recalculating a profile if it already exists.  On cache miss an **Anthropic
API key** is required, but callers *never* supply it – the key is read from
the `ANTHROPIC_API_KEY` environment variable by the library itself.

> **Note:** the code no longer overrides Claude's temperature; we rely on the
> model default per the product requirement.  A structured output header is
> included in the prompt following the Anthropic documentation.

---

## API

This project exposes a very small REST interface implemented with [FastAPI](https://fastapi.tiangolo.com/).

```http
GET /users/{user_id}/profile?date=2026-03-04&api_key=...
```

- `user_id` path parameter – the ID of the user to look up.
- `date` query parameter – optional ISO date.  Defaults to today.

The service obtains the Anthropic API key from the environment; callers do
not need to supply one explicitly.

A simple health check is available at `GET /health`.

### REST vs gRPC

The current implementation is REST because:

1. We already have a lightweight HTTP stack (FastAPI + uvicorn) and the data
   model is JSON, which maps naturally to REST.
2. Latency is dominated by the LLM and database I/O; the difference between a
   gRPC binary payload and a JSON POST would be negligible.
3. Operational simplicity: most teams are familiar with REST, and exposing a
   schema-documented OpenAPI spec (automatic with FastAPI) is convenient.

For very high throughput or when supporting mobile clients with strict
bandwidth budgets, a gRPC/Protobuf API could be added later.  The service
layer (e.g. the `get_user_taste_profile` function) is agnostic to the
transport; only the adapter would need to be rewritten.

---

## Running the service

Install dependencies with `pip install -r requirements.txt` (or use
`pyproject.toml` with `pip install .`).

#### Configuration via environment variables

The library reads the following variables when constructing the database
connection and selecting the LLM model.  Defaults match the development
environment but can be overridden in production.

* `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_NAME` – MySQL
  credentials and host.  If you use a different database system you'll need to
  adapt `get_engine()`.
* `ANTHROPIC_MODEL` – Claude model name (defaults to the haiku variant).  Do
  **not** codify a temperature here; the code relies on the model default.
* `ANTHROPIC_API_KEY` – your Claude API key.  It may also be passed in the
  query parameter of the API call on cache miss.

Start the server with:

```bash
uvicorn vasuvi.server:app --host 0.0.0.0 --port 8000
```

The OpenAPI schema (and interactive docs) will be available at
`http://localhost:8000/docs`.

You can also call the library directly from another script, for example:

```python
from vasuvi import get_user_taste_profile

profile = get_user_taste_profile(12345, api_key="sk-..." )
print(profile)
```

---

## Notes & Next steps

* The caching layer uses MySQL JSON type; if you plan to move to Postgres you
  can rework `ensure_cache_table` accordingly.
* Backfilling older dates can be done by calling the library in a batch
  job and specifying the `as_of` parameter.
* The service currently has no authentication; a real deployment should
  protect API keys and consider rate limiting.
* For reproducibility we pin dependencies in `pyproject.toml`/requirements.

#### Development convenience

Set `USE_EXCEL_CACHE=1` (and optionally `EXCEL_CACHE_PATH`) in your
environment to bypass the MySQL database entirely.  Profiles will be stored
in a simple CSV file at the given path.  This is handy for quick local work
when a database server is not available.

### Scaling considerations

- **Horizontal scaling**: the FastAPI app is stateless; you can spin up
  multiple Uvicorn workers or deploy behind a Kubernetes `Deployment`/`ECS`
  service.  The database cache table ensures that only the first request for a
  user/date hits Claude.
- **Connection pooling**: not applicable when using the CSV-only cache.
  There is no database connection in the development configuration.
- **Batching & backfill**: a separate job can iterate over user IDs and call
  `get_user_taste_profile(..., as_of=some_date)` to warm the cache ahead of
  time; this keeps the interactive API latency down.

Happy coding!  🎯
