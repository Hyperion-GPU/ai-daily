from collections.abc import Iterable

DEFAULT_CATEGORY = "general"


def resolve_category(
    topics: Iterable[str] | None,
    category_map: dict[str, list[str]] | None = None,
) -> str:
    normalized_topics = {
        str(topic).strip().casefold()
        for topic in (topics or [])
        if isinstance(topic, str) and topic.strip()
    }
    if not normalized_topics:
        return DEFAULT_CATEGORY

    for category, category_topics in (category_map or {}).items():
        if any(str(topic).strip().casefold() in normalized_topics for topic in category_topics):
            return category

    return DEFAULT_CATEGORY
