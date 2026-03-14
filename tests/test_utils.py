from src.utils import clean_html_tags, truncate_text


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

