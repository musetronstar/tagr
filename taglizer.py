from __future__ import annotations

from parser import Relation, TranslationError


def taglize_relation(relation: Relation) -> str:
    """Translate a parsed relation into a TAGL put statement."""
    return f">> {relation.subject} {relation.relator} {relation.obj};"


def taglize_relations(relations: list[Relation]) -> str:
    """Translate one or more parsed relations into TAGL output."""
    if not relations:
        raise TranslationError("Unsupported input: no relation to emit")

    if len(relations) == 1:
        return taglize_relation(relations[0])

    subject = relations[0].subject
    lines = [f">> {subject} {relations[0].relator} {relations[0].obj}"]

    for relation in relations[1:]:
        if relation.subject == subject:
            lines.append(f"{relation.relator} {relation.obj}")
        else:
            lines.append(f">> {relation.subject} {relation.relator} {relation.obj}")

    lines[-1] = f"{lines[-1]};"
    return "\n".join(lines)


def rule_relation(relation: Relation) -> str:
    """Compatibility wrapper for earlier naming."""
    return taglize_relation(relation)


def rule_relations(relations: list[Relation]) -> str:
    """Compatibility wrapper for earlier naming."""
    return taglize_relations(relations)
