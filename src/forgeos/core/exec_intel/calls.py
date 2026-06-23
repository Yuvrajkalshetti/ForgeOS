"""Python call-site extraction for Execution Intelligence (ADR 0015, E2).

Pure ``ast`` — no execution. Per file it returns (1) the import bindings (local name ->
``(module, original name)``) and (2) the raw call sites, each attributed to its enclosing
function/method node id (or the file node for module-level calls). Resolving a call site
to a target symbol is the engine's job (it needs the whole-repo symbol index).
"""

from __future__ import annotations

import ast
from dataclasses import dataclass


@dataclass(frozen=True)
class RawCall:
    """An unresolved call site: caller + the syntactic shape of the callee."""

    caller_id: str
    name: str | None  # bare ``name()``
    attr: str | None  # ``<base>.attr()`` or ``self.attr()``
    base: str | None  # the ``<base>`` in ``base.attr()`` (None for self/bare)
    via_self: bool  # ``self.attr()``
    cls: str | None  # enclosing class label (qualname), for ``self`` resolution


def _raw_call(func: ast.expr, caller_id: str, cls: str | None) -> RawCall:
    if isinstance(func, ast.Name):
        return RawCall(caller_id, func.id, None, None, False, cls)
    if isinstance(func, ast.Attribute):
        base = func.value
        if isinstance(base, ast.Name) and base.id == "self":
            return RawCall(caller_id, None, func.attr, None, True, cls)
        if isinstance(base, ast.Name):
            return RawCall(caller_id, None, func.attr, base.id, False, cls)
        return RawCall(caller_id, None, func.attr, None, False, cls)
    return RawCall(caller_id, None, None, None, False, cls)


def _collect_imports(tree: ast.Module) -> dict[str, tuple[str, str | None]]:
    imports: dict[str, tuple[str, str | None]] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.asname:
                    imports[alias.asname] = (alias.name, None)
                else:
                    top = alias.name.split(".")[0]
                    imports[top] = (top, None)
        elif isinstance(node, ast.ImportFrom) and node.module is not None and node.level == 0:
            for alias in node.names:
                imports[alias.asname or alias.name] = (node.module, alias.name)
    return imports


def analyze_calls(
    file: str, source: str
) -> tuple[dict[str, tuple[str, str | None]], list[RawCall]]:
    """Return (import bindings, raw call sites) for one Python source file."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return {}, []
    imports = _collect_imports(tree)
    calls: list[RawCall] = []
    file_id = f"file:{file}"

    def visit(node: ast.AST, caller_id: str, cls: str | None, prefix: str) -> None:
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            inner = f"{prefix}{node.name}"
            for child in node.body:
                visit(child, f"func:{file}#{inner}", cls, f"{inner}.")
            return
        if isinstance(node, ast.ClassDef):
            label = f"{prefix}{node.name}"
            for child in node.body:
                visit(child, file_id, label, f"{label}.")
            return
        if isinstance(node, ast.Call):
            calls.append(_raw_call(node.func, caller_id, cls))
        for child in ast.iter_child_nodes(node):
            visit(child, caller_id, cls, prefix)

    visit(tree, file_id, None, "")
    return imports, calls
