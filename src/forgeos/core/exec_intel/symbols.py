"""Deterministic Python symbol extraction (ADR 0015, E1).

Pure ``ast`` walk — no execution, no provider, no network. Produces Function/Method/
Class nodes with stable ids and DEFINES edges from each enclosing scope. Class base
names are recorded in ``props['bases']`` for the engine to resolve into EXTENDS edges
across the whole repository.
"""

from __future__ import annotations

import ast

from forgeos.core.exec_intel.models import (
    Confidence,
    ExecEdge,
    ExecEdgeType,
    ExecNode,
    ExecNodeType,
)


def _base_name(expr: ast.expr) -> str | None:
    """Return the simple name of a class base expression, or ``None``."""
    if isinstance(expr, ast.Name):
        return expr.id
    if isinstance(expr, ast.Attribute):
        return expr.attr
    return None


def _defines_edge(src_id: str, dst_id: str) -> ExecEdge:
    return ExecEdge(
        id=f"{src_id}|defines|{dst_id}",
        src_id=src_id,
        dst_id=dst_id,
        type=ExecEdgeType.DEFINES,
        confidence=Confidence.EXACT,
    )


def extract_symbols(file: str, source: str) -> tuple[list[ExecNode], list[ExecEdge]]:
    """Return ``(nodes, edges)`` for one Python source file; empty on syntax error."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return [], []
    nodes: list[ExecNode] = []
    edges: list[ExecEdge] = []
    file_id = f"file:{file}"

    def walk(body: list[ast.stmt], parent_id: str, prefix: str, in_class: bool) -> None:
        for stmt in body:
            if isinstance(stmt, ast.FunctionDef | ast.AsyncFunctionDef):
                qual = f"{prefix}{stmt.name}"
                node_id = f"func:{file}#{qual}"
                node_type = ExecNodeType.METHOD if in_class else ExecNodeType.FUNCTION
                nodes.append(
                    ExecNode(
                        id=node_id, type=node_type, label=qual, file=file, lineno=stmt.lineno
                    )
                )
                edges.append(_defines_edge(parent_id, node_id))
                walk(stmt.body, node_id, f"{qual}.", False)
            elif isinstance(stmt, ast.ClassDef):
                qual = f"{prefix}{stmt.name}"
                node_id = f"class:{file}#{qual}"
                bases: list[str] = []
                for base in stmt.bases:
                    name = _base_name(base)
                    if name is not None:
                        bases.append(name)
                nodes.append(
                    ExecNode(
                        id=node_id,
                        type=ExecNodeType.CLASS,
                        label=qual,
                        file=file,
                        lineno=stmt.lineno,
                        props={"bases": bases, "simple_name": stmt.name},
                    )
                )
                edges.append(_defines_edge(parent_id, node_id))
                walk(stmt.body, node_id, f"{qual}.", True)

    walk(tree.body, file_id, "", False)
    return nodes, edges
