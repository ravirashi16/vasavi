from vasuvi.processor import prepare_step2_markdown

def test_prepare_step2_markdown_simple():
    posts = [
        {"user_id": 1, "post_category_id": 2, "msg": "Hello #tag", "location_name": "Loc", "latitude": 0, "longitude": 0, "rating": 4, "created_on": "2024-01-01 12:00:00"}
    ]
    md = prepare_step2_markdown(posts, {2: "tv"}, recent_days=365)
    assert "Category: Tv" in md
    assert "Hello" in md
