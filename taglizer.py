from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from parser import Relation


def _translation_error_cls() -> type[Exception]:
    from parser import TranslationError

    return TranslationError


def _taglize(text: str | tuple[str, ...]) -> str:
    """Convert relation text to TAGL id form (`x y` -> `x_y`)."""
    if isinstance(text, tuple):
        text = " ".join(text)
    return "_".join(text.lower().split())


def _format_object(obj: object) -> str:
    from parser import QuantifiedObject

    if isinstance(obj, QuantifiedObject):
        return f"{obj.quantified_obj.lower()} = {obj.qty.lower()}, {obj.trailing_obj.lower()}"
    return str(obj).lower()


def taglize_relation(relation: Relation) -> str:
    """Translate a parsed relation into a TAGL put statement."""
    return (
        f">> {relation.subject.lower()} "
        f"{_taglize(relation.relator)} "
        f"{_format_object(relation.obj)};"
    )


def taglize_relations(relations: list[Relation]) -> str:
    """Translate one or more parsed relations into TAGL output."""
    if not relations:
        raise _translation_error_cls()("Unsupported input: no relation to emit")

    if len(relations) == 1:
        return taglize_relation(relations[0])

    subject = relations[0].subject.lower()
    lines = [
        f">> {subject} {_taglize(relations[0].relator)} {_format_object(relations[0].obj)}"
    ]

    for relation in relations[1:]:
        if relation.subject.lower() == subject:
            lines.append(f"{_taglize(relation.relator)} {_format_object(relation.obj)}")
        else:
            lines.append(
                f">> {relation.subject.lower()} "
                f"{_taglize(relation.relator)} "
                f"{_format_object(relation.obj)}"
            )

    lines[-1] = f"{lines[-1]};"
    return "\n".join(lines)
