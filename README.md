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

## Use inside Claude (MCP)
ForgeOS ships an optional **MCP server** (`forgeos-mcp`) so a Claude host — Claude Code or
Claude Desktop — can call ForgeOS as tools mid-conversation. It is a thin transport over the
same services as the CLI (ADR 0007); no business logic lives in it, and the `mcp` dependency
is optional (the `forge`/`forgeos` CLI never imports it).

**All seven tools are read-only and require no LLM provider** — in the MCP model the host
(Claude Code) is the reasoning model (ADR 0014). No API key, no Ollama:

- `forgeos_status`, `forgeos_doctor` — project state + readiness diagnostics
- `forgeos_skill_list`, `forgeos_skill_show` — inspect promoted skills
- `forgeos_graph_summary` — traverse the knowledge graph
- `forgeos_memory_summary` — query stored memory
- `forgeos_advisory_context` — assemble Mentor's deterministic, provider-free grounding
  bundle (cards, memory, ADRs, repo profile, decisions, findings) for the host model to
  reason over

Install the optional extra and note the server path:
```bash
uv sync --extra mcp                 # from a clone;  or:  uv tool install ".[mcp]"
uv run which forgeos-mcp            # copy this absolute path for the steps below
```

**Claude Code:**
```bash
# register once (use the absolute path from `which` above; add -s user for all projects)
claude mcp add forgeos -- /ABS/PATH/TO/.venv/bin/forgeos-mcp
claude mcp list                     # confirm it is registered + connected

cd /path/to/your/project && claude  # tools default to project="." = the launch directory
# inside the session:  /mcp         # confirms `forgeos` is connected (7 tools)
```
Then ask in plain language, e.g. *"using forgeos, show status and run doctor"*, or
*"using forgeos, get the advisory context for the memory module and review it"* — Claude
Code reasons over the grounding the tool returns. If you start `claude` outside the
project, name the path instead: *"run forgeos_status for project /path/to/project"*.

**Claude Desktop:** add to `~/Library/Application Support/Claude/claude_desktop_config.json`,
then fully restart Claude Desktop:
```json
{ "mcpServers": { "forgeos": { "command": "/ABS/PATH/TO/.venv/bin/forgeos-mcp", "args": [] } } }
```
Pass the project path in chat since the server's working directory may differ.

## Layout
```
src/forgeos/
  config/         layered configuration (defaults -> ~/.forgeos -> project/.forgeos -> env)
  observability/  structured logging with request correlation
  ports/          abstract interfaces (storage, provider, transport, tokenizer, vector)
  adapters/       concrete implementations (transport/cli, transport/mcp, ... )
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
