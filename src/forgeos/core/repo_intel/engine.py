"""Repository Intelligence engine: scan a repo into the knowledge graph.

Deterministic and **provider-free** (ADR 0005): no provider/LLM calls. Incremental
via content hashes — unchanged files reuse their cached parse, so only changed
files are re-parsed. Emits File/Module/Dependency nodes with ``contains`` and
``depends_on`` edges, plus a compact ``RepoProfile``.
"""

from __future__ import annotations

import datetime
import hashlib
from collections.abc import Callable
from pathlib import Path

from forgeos._time import utcnow
from forgeos.catalog import Collections
from forgeos.core.graph import EdgeType, GraphStore, NodeType
from forgeos.core.graph.store import Direction
from forgeos.core.repo_intel.deps import extract_imports, is_stdlib
from forgeos.core.repo_intel.hotspots import ChurnSource, null_churn, rank_hotspots
from forgeos.core.repo_intel.models import FileRecord, RepoProfile, ScanResult
from forgeos.core.repo_intel.scanner import iter_source_files
from forgeos.ports.storage import StoragePort

Clock = Callable[[], datetime.datetime]


def _file_id(rel: str) -> str:
    return f"file:{rel}"


def _module_id(dir_rel: str) -> str:
    return f"mod:{dir_rel}"


def _dep_id(name: str) -> str:
    return f"dep:{name}"


class RepoIntelEngine:
    """Scan repositories into the graph. Constructed without any provider."""

    def __init__(
        self,
        graph: GraphStore,
        store: StoragePort,
        churn: ChurnSource = null_churn,
        clock: Clock = utcnow,
    ) -> None:
        self._graph = graph
        self._store = store
        self._churn = churn
        self._clock = clock

    def scan(self, root: Path) -> ScanResult:
        """Ingest ``root`` and return a summary. Re-parses only changed files."""
        scanned = iter_source_files(root)
        stored = {
            r["path"]: FileRecord.model_validate(r)
            for r in self._store.query(Collections.REPO_INDEX)
        }

        records: dict[str, FileRecord] = {}
        parsed = reused = 0
        for sf in scanned:
            prior = stored.get(sf.path)
            if prior is not None and prior.hash == sf.content_hash:
                records[sf.path] = prior
                reused += 1
                continue
            source = (root / sf.path).read_text(encoding="utf-8", errors="replace")
            record = FileRecord(
                path=sf.path,
                hash=sf.content_hash,
                language=sf.language,
                size=sf.size,
                raw_imports=extract_imports(sf.language, source),
            )
            records[sf.path] = record
            self._store.put(Collections.REPO_INDEX, sf.path, record.model_dump(mode="json"))
            parsed += 1

        removed = sorted(set(stored) - set(records))
        for path in removed:
            self._store.delete(Collections.REPO_INDEX, path)
            self._graph.remove_node(_file_id(path))

        packages = self._packages(records)
        internal_edges, external_deps = self._emit(records, packages)
        self._prune_orphans()
        self._write_profile(root, records, packages)

        return ScanResult(
            files=len(records),
            modules=len(packages),
            internal_edges=len(internal_edges),
            external_deps=len(external_deps),
            parsed=parsed,
            reused=reused,
            removed=len(removed),
            hotspots=[h.path for h in rank_hotspots(self._churn(root))],
        )

    # -- helpers ---------------------------------------------------------------
    @staticmethod
    def _packages(records: dict[str, FileRecord]) -> dict[str, str]:
        """Map package label -> directory relpath (dirs containing ``__init__.py``)."""
        packages: dict[str, str] = {}
        for path in records:
            p = Path(path)
            if p.name == "__init__.py":
                dir_rel = p.parent.as_posix()
                packages[p.parent.name] = dir_rel
        return packages

    @staticmethod
    def _package_of(path: str, packages: dict[str, str]) -> str | None:
        """Return the deepest package directory containing ``path``, if any."""
        best: str | None = None
        for dir_rel in packages.values():
            matches = path == f"{dir_rel}/{Path(path).name}" or path.startswith(f"{dir_rel}/")
            if matches and (best is None or len(dir_rel) > len(best)):
                best = dir_rel
        return best

    def _emit(
        self, records: dict[str, FileRecord], packages: dict[str, str]
    ) -> tuple[set[tuple[str, str]], set[str]]:
        internal: set[tuple[str, str]] = set()
        external: set[str] = set()
        for path, record in sorted(records.items()):
            file_id = _file_id(path)
            self._graph.upsert_node(
                NodeType.FILE,
                label=path,
                props={"language": record.language, "size": record.size, "hash": record.hash},
                node_id=file_id,
            )
            own_dir = self._package_of(path, packages)
            own_label = Path(own_dir).name if own_dir is not None else None
            if own_dir is not None:
                module_id = _module_id(own_dir)
                self._graph.upsert_node(
                    NodeType.MODULE, label=own_label or own_dir, node_id=module_id
                )
                self._graph.add_edge(module_id, file_id, EdgeType.CONTAINS)
            self._emit_deps(record, file_id, own_label, packages, internal, external)
        return internal, external

    def _emit_deps(
        self,
        record: FileRecord,
        file_id: str,
        own_label: str | None,
        packages: dict[str, str],
        internal: set[tuple[str, str]],
        external: set[str],
    ) -> None:
        for imp in record.raw_imports:
            if record.language == "python":
                if is_stdlib(imp):
                    continue
                if imp in packages and imp != own_label:
                    module_id = _module_id(packages[imp])
                    self._graph.upsert_node(NodeType.MODULE, label=imp, node_id=module_id)
                    self._graph.add_edge(file_id, module_id, EdgeType.DEPENDS_ON)
                    internal.add((file_id, module_id))
                elif imp not in packages:
                    self._add_external(file_id, imp, external)
            elif record.language in ("javascript", "typescript") and not imp.startswith("."):
                self._add_external(file_id, imp, external)

    def _add_external(self, file_id: str, name: str, external: set[str]) -> None:
        dep_id = _dep_id(name)
        self._graph.upsert_node(NodeType.DEPENDENCY, label=name, node_id=dep_id)
        self._graph.add_edge(file_id, dep_id, EdgeType.DEPENDS_ON)
        external.add(name)

    def _prune_orphans(self) -> None:
        for node_type in (NodeType.MODULE, NodeType.DEPENDENCY):
            for node in self._graph.nodes(node_type):
                if not self._graph.neighbors(node.id, direction=Direction.BOTH):
                    self._graph.remove_node(node.id)

    def _write_profile(
        self, root: Path, records: dict[str, FileRecord], packages: dict[str, str]
    ) -> None:
        digest = hashlib.sha256()
        for path in sorted(records):
            digest.update(f"{path}:{records[path].hash}".encode())
        languages = sorted({r.language for r in records.values() if r.language})
        profile = RepoProfile(
            root=root.name,
            languages=languages,
            file_count=len(records),
            module_count=len(packages),
            hotspots=rank_hotspots(self._churn(root)),
            scanned_at=self._clock().isoformat(),
            index_hash=digest.hexdigest(),
        )
        self._store.put(Collections.REPO_PROFILE, "profile", profile.model_dump(mode="json"))
