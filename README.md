# ForgeOS

A **local-first AI Operating System** that sits between users, projects, and AI providers.
Its purpose is to **preserve knowledge while sending fewer tokens** via intelligent memory,
knowledge graphs, context compression, and explainable agent orchestration.

> Status: **V1.0.0** — build complete, CLI-first. See `docs/ARCHITECTURE.md` and
> `docs/IMPLEMENTATION_PLAN.md`; architectural decisions are recorded in `docs/adr/`;
> per-release changes in `CHANGELOG.md`.
>
> **Known limitation (V1.0.0):** the Claude and Ollama provider adapters are implemented
> and unit-tested, but live end-to-end validation (real Claude/Ollama generate + token
> reconciliation against provider-reported usage) is **post-release validation** — it
> requires network + API key / a local Ollama and was not run in the build environment.

## Principles
- **Token efficiency first** — every feature must justify its token cost.
- **Human-controlled learning** — nothing is promoted or self-modified without approval.
- **Local-first, cloud-optional** — knowledge is the asset; the runtime is disposable.
- **Adapter-first** — providers, storage, and transports are swappable behind ports.

## Quickstart
Install (idempotent; installs `uv` if needed and exposes the `forgeos`/`forge` command):
```bash
bash install.sh          # macOS / Linux
# or:  pwsh -File install.ps1   (Windows)
# or, manually, from a clone:   uv tool install .
```

Initialize a workspace and check your install:
```bash
forgeos init             # create .forgeos/ in the current project (idempotent, non-destructive)
forgeos doctor           # verify environment + config
forgeos status           # show workspace state at a glance
forgeos wizard           # guided first-run walkthrough
```

Build knowledge, then drive the human-gated learning loop:
```bash
forgeos scan .                      # index the repo into memory + knowledge graph
forgeos memory query "<text>"       # query stored memory
forgeos graph query "<text>"        # query the knowledge graph (graph why <id> explains an edge)
forgeos mentor "<question>"         # advisory guidance (read-only; never executes)
forgeos audit                       # advisory audit of the current state

forgeos learn review                # list proposals awaiting a decision (nothing auto-promotes)
forgeos learn approve <id> --actor you
forgeos learn commit  <id> --actor you   # approved learning -> Skill node
forgeos skill list                  # list promoted skills
forgeos skill show <id>             # inspect a skill

forgeos export <path>               # portability: export workspace
forgeos import <path>               # import a workspace
forgeos backup                      # snapshot with retention pruning
```

> `forge` and `forgeos` are the same CLI (two console aliases). Run `forgeos --help` for
> the full command surface.

## Layout
```
src/forgeos/
  config/         layered configuration (defaults -> ~/.forgeos -> project/.forgeos -> env)
  observability/  structured logging with request correlation
  ports/          abstract interfaces (storage, provider, transport, tokenizer, vector)
  adapters/       concrete implementations (transport/cli, ... )
  testing/        in-memory fakes + static guards for tests
docs/             architecture, implementation plan, ADRs
tests/            unit tests + golden repository corpus
```

## Toolchain
Python 3.12 · uv · ruff · mypy (strict on `src/`) · pytest.

```bash
uv sync --extra dev      # create env + install
uv run ruff check .      # lint
uv run mypy              # type-check
uv run pytest            # tests
forge --help             # CLI
```

When `ruff`/`mypy` are unavailable in a constrained environment, `python scripts/check.py`
provides a stdlib-only substitute (syntax + annotation + import hygiene checks).
