"""Static state-access extraction + resolution measurement (E5A, ADR 0017).

Pure ast, deterministic. EMITS only ``self.<attr>`` READS/WRITES (Store=write, Load=read)
— the receiver type (the enclosing class) is the one type known without inference. For
**every** ``recv.attr`` access it also MEASURES how it would resolve under the conservative
TypeEnv rules (self / parameter+local annotation / direct constructor binding), purely to
count effectiveness — it does NOT emit annotation/constructor edges (that is E5B).

No SSA, no symbolic execution, no alias analysis, no dynamic dispatch, no inference beyond
the TypeEnv. The env is flow-insensitive (conservative).
"""

from __future__ import annotations

import ast
from dataclasses import dataclass

from forgeos.core.dataflow_intel.models import DfEdgeType, StateSymbol

_Env = dict[str, tuple[str, str]]  # local name -> (type name, source: annotation|constructor)


@dataclass
class _Access:
    caller_id: str
    state_id: str
    edge: DfEdgeType


class StateExtractor:
    """Walk one file: emit self-attr edges and measure resolution effectiveness."""

    def __init__(self, file: str) -> None:
        self.file = file
        self.nodes: dict[str, StateSymbol] = {}
        self.accesses: list[_Access] = []
        self.total_attr = 0
        self.resolved_self = 0
        self.resolved_annotation = 0
        self.resolved_constructor = 0
        self.unresolved = 0

    def run(self, tree: ast.Module) -> None:
        self._visit(tree, f"file:{self.file}", None, "", {})

    # -- traversal -------------------------------------------------------------
    def _visit(
        self, node: ast.AST, caller_id: str, cls: str | None, prefix: str, env: _Env
    ) -> None:
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            qual = f"{prefix}{node.name}"
            fenv = self._build_env(node)
            for stmt in node.body:
                self._visit(stmt, f"func:{self.file}#{qual}", cls, f"{qual}.", fenv)
            return
        if isinstance(node, ast.ClassDef):
            label = f"{prefix}{node.name}"
            self._class_attrs(node, label)
            for stmt in node.body:
                self._visit(stmt, caller_id, label, f"{label}.", {})
            return
        if isinstance(node, ast.Attribute):
            self._classify(node, caller_id, cls, env)
        for sub in ast.iter_child_nodes(node):
            self._visit(sub, caller_id, cls, prefix, env)

    # -- measurement + emission ------------------------------------------------
    def _classify(
        self, node: ast.Attribute, caller_id: str, cls: str | None, env: _Env
    ) -> None:
        self.total_attr += 1
        value = node.value
        if not isinstance(value, ast.Name):
            self.unresolved += 1
            return
        if value.id == "self" and cls is not None:
            self.resolved_self += 1
            self._emit(node, caller_id, cls)
            return
        binding = env.get(value.id)
        if binding is None:
            self.unresolved += 1
        elif binding[1] == "constructor":
            self.resolved_constructor += 1
        else:
            self.resolved_annotation += 1

    def _emit(self, node: ast.Attribute, caller_id: str, cls: str) -> None:
        state_id = f"state:{self.file}#{cls}.{node.attr}"
        self.nodes[state_id] = StateSymbol(
            id=state_id, kind="attr", label=f"{cls}.{node.attr}", file=self.file
        )
        edge = DfEdgeType.WRITES if isinstance(node.ctx, ast.Store) else DfEdgeType.READS
        self.accesses.append(_Access(caller_id, state_id, edge))

    def _class_attrs(self, node: ast.ClassDef, label: str) -> None:
        for stmt in node.body:
            target: ast.expr | None = None
            if isinstance(stmt, ast.AnnAssign):
                target = stmt.target
            elif isinstance(stmt, ast.Assign) and len(stmt.targets) == 1:
                target = stmt.targets[0]
            if isinstance(target, ast.Name):
                state_id = f"state:{self.file}#{label}.{target.id}"
                self.nodes[state_id] = StateSymbol(
                    id=state_id, kind="attr", label=f"{label}.{target.id}", file=self.file
                )

    # -- TypeEnv (conservative, flow-insensitive) ------------------------------
    def _build_env(self, fn: ast.FunctionDef | ast.AsyncFunctionDef) -> _Env:
        env: _Env = {}
        for arg in (*fn.args.posonlyargs, *fn.args.args, *fn.args.kwonlyargs):
            type_name = _anno_type(arg.annotation)
            if type_name is not None and arg.arg != "self":
                env[arg.arg] = (type_name, "annotation")
        for stmt in fn.body:
            self._collect(stmt, env)
        return env

    def _collect(self, node: ast.AST, env: _Env) -> None:
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            return  # do not enter nested scopes
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            type_name = _anno_type(node.annotation)
            if type_name is not None:
                env[node.target.id] = (type_name, "annotation")
        elif isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name):
                ctor = _call_type(node.value)
                if ctor is not None:
                    env[target.id] = (ctor, "constructor")
                else:
                    env.pop(target.id, None)
        for sub in ast.iter_child_nodes(node):
            self._collect(sub, env)


def _anno_type(annotation: ast.expr | None) -> str | None:
    if isinstance(annotation, ast.Name):
        return annotation.id
    if isinstance(annotation, ast.Attribute):
        return annotation.attr
    return None


def _call_type(value: ast.expr) -> str | None:
    if not isinstance(value, ast.Call):
        return None
    func = value.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


def extract_state(file: str, source: str) -> StateExtractor:
    """Return a populated :class:`StateExtractor` for one Python file."""
    extractor = StateExtractor(file)
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return extractor
    extractor.run(tree)
    return extractor
