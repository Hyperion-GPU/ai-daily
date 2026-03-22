from src.utils import clean_html_tags, split_by_ratio, truncate_text


def test_clean_html_tags_handles_nested_tags_and_entities():
    text = "<p>Hello <strong>AI</strong>&nbsp;&amp;&nbsp;<em>ML</em></p>"
    assert clean_html_tags(text) == "Hello AI & ML"


def test_clean_html_tags_handles_empty_and_plain_text():
    assert clean_html_tags("") == ""
    assert clean_html_tags(None) == ""
    assert clean_html_tags("plain text") == "plain text"


def test_truncate_text_respects_boundary():
    assert truncate_text("hello", 5) == "hello"
    assert truncate_text("hello world", 5) == "hello..."


def test_truncate_text_handles_empty_values():
    assert truncate_text("", 5) == ""
    assert truncate_text(None, 5) == ""


def test_split_by_ratio_keeps_primary_share():
    items = [
        {"id": "n1", "kind": "news", "score": 2},
        {"id": "a1", "kind": "arxiv", "score": 5},
        {"id": "n2", "kind": "news", "score": 1},
        {"id": "a2", "kind": "arxiv", "score": 4},
    ]

    result = split_by_ratio(items, 0.5, 4, is_primary=lambda item: item["kind"] != "arxiv")

    assert [item["id"] for item in result] == ["n1", "n2", "a1", "a2"]


def test_split_by_ratio_sorts_each_bucket_when_requested():
    items = [
        {"id": "a-low", "kind": "arxiv", "score": 1},
        {"id": "n-low", "kind": "news", "score": 2},
        {"id": "a-high", "kind": "arxiv", "score": 5},
        {"id": "n-high", "kind": "news", "score": 4},
    ]

    result = split_by_ratio(
        items,
        0.5,
        4,
        is_primary=lambda item: item["kind"] != "arxiv",
        sort_key=lambda item: item["score"],
        reverse=True,
    )

    assert [item["id"] for item in result] == ["n-high", "n-low", "a-high", "a-low"]
