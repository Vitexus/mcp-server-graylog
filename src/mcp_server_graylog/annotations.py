"""Annotation helpers: classify upstream tools and fill missing hints."""

from mcp_types import ToolAnnotations

READ_ONLY_ANNOTATIONS = ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True)
CREATE_ANNOTATIONS = ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=False, open_world_hint=True)
MUTATE_ANNOTATIONS = ToolAnnotations(read_only_hint=False, destructive_hint=True, idempotent_hint=True, open_world_hint=True)

_READ_PREFIXES = ("get_", "list_", "search_", "find_", "query_", "show_", "describe_", "count_", "read_", "fetch_")
_CREATE_PREFIXES = ("create_", "add_", "send_", "post_", "start_", "run_", "trigger_")


def title_from_name(name: str) -> str:
    return name.replace("_", " ").replace("-", " ").strip().title()


def classify(name: str) -> ToolAnnotations:
    """Fallback for tools whose upstream annotations are missing (fail closed)."""
    lowered = name.lower()
    if lowered.startswith(_READ_PREFIXES):
        return READ_ONLY_ANNOTATIONS
    if lowered.startswith(_CREATE_PREFIXES):
        return CREATE_ANNOTATIONS
    return MUTATE_ANNOTATIONS


def complete(name: str, ann: ToolAnnotations | None) -> ToolAnnotations:
    """Keep every upstream hint; fill only the ones Graylog left unset."""
    fallback = classify(name)
    if ann is None:
        return fallback
    return ToolAnnotations(
        title=ann.title,
        read_only_hint=fallback.read_only_hint if ann.read_only_hint is None else ann.read_only_hint,
        destructive_hint=fallback.destructive_hint if ann.destructive_hint is None else ann.destructive_hint,
        idempotent_hint=fallback.idempotent_hint if ann.idempotent_hint is None else ann.idempotent_hint,
        open_world_hint=True if ann.open_world_hint is None else ann.open_world_hint,
    )
