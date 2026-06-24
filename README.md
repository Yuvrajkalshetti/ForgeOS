# ForgeOS

A **local-first AI Operating System** that sits between you, your projects, and AI models.
It **preserves project knowledge while sending fewer tokens** — giving your AI assistant a
persistent memory, a knowledge graph of your codebase, deterministic **code intelligence**
(call graph, ownership, data flow), compact context “cards,” and an explainable, human-gated
learning loop.

Use it two ways, together or separately:

- **CLI** (`forgeos` / `forge`) — build and query the knowledge directly in your terminal.
- **Inside Claude (MCP)** — Claude Code / Claude Desktop call ForgeOS as **18 read-only tools**,
  so the assistant reasons with *your* accumulated project knowledge. **No API key or extra
  model required** — your Claude host is the model.

> Status: **V1.0.0** (CLI-first) + **V2** MCP & Code Intelligence (Execution / Ownership /
> Data Flow). Current status & roadmap: `docs/ROADMAP.md`; architecture in `docs/ARCHITECTURE.md`;
> decisions in `docs/adr/`; changes in `CHANGELOG.md`.

---

## Requirements

- **Python 3.12+**
- **[uv](https://docs.astral.sh/uv/)** — the installer below sets it up if it's missing
- **git** — used when indexing a repository
- macOS, Linux, or Windows
- **No AI provider or API key** is needed for the CLI's core commands or for any of the
  Claude (MCP) tools. A provider (Claude API **or** a local [Ollama](https://ollama.com)) is
  only required for the provider-backed `forge mentor` / `audit` CLI commands — never for MCP.

---

## Install

From a clone of this repo, the quickest path (installs `uv` if needed and exposes the
`forgeos`/`forge` commands):

```bash
bash install.sh            # macOS / Linux
pwsh -File install.ps1     # Windows
```

Or install directly with uv — use this form to also get the MCP server (`forgeos-mcp`):

```bash
uv tool install ".[mcp]"   # installs forgeos, forge, and forgeos-mcp on your PATH
```

Verify:

```bash
forgeos --help
forgeos doctor             # checks Python, config, and (optional) provider setup
```

> `forge` and `forgeos` are the same CLI (two console aliases).

---

## First 5 minutes

ForgeOS starts **empty** — you feed it knowledge, then query it. (A fresh workspace showing
all-zero counts is normal, not a bug.) In any project:

```bash
cd /path/to/your/project
forgeos init                     # create .forgeos/ (idempotent, non-destructive)
forgeos sync                     # scan + compress + exec-scan in one step (provider-free)
forgeos memory add "We use uv + hatchling; mypy strict on src/"   # remember a fact
forgeos status                   # counts should now be non-zero
```

`forgeos sync` is the one-shot seeder/refresher. (The individual steps — `forgeos scan`,
`forgeos compress run --bulk`, `forgeos exec-scan` — still exist if you want to run them
separately.) Query what it now knows:

```bash
forgeos memory query                  # list stored memory (filter with --scope / --kind)
forgeos graph query <file-or-label>   # explore the graph (`graph why <id>` explains an edge)
forgeos skill list                    # skills promoted via the learning loop
```

---

## Use inside Claude (MCP)

ForgeOS ships an optional **MCP server** (`forgeos-mcp`) so a Claude host — Claude Code or
Claude Desktop — can call ForgeOS as tools mid-conversation. It's a thin transport over the
same services as the CLI (ADR 0007); the `mcp` dependency is optional and the `forge`/`forgeos`
CLI never imports it.

**All 18 tools are read-only and need no LLM provider** — in the MCP model your Claude host is
the reasoning model.

**Knowledge (7)** — wrap V1 services:

| Tool | Returns |
|------|---------|
| `forgeos_status` | project state + record counts + active provider |
| `forgeos_doctor` | environment / readiness diagnostics |
| `forgeos_skill_list` / `forgeos_skill_show` | promoted skills |
| `forgeos_graph_summary` | nodes reachable from a target in the knowledge graph |
| `forgeos_memory_summary` | stored memory records (optionally filtered) |
| `forgeos_advisory_context` | deterministic, provider-free **grounding bundle** for the host model to reason over |

**Execution Intelligence (4)** — the call graph (needs `forgeos sync`/`exec-scan` first):

| Tool | Answers |
|------|---------|
| `forgeos_symbol` | find a function/method/class by name |
| `forgeos_call_graph` | callers or callees of a symbol |
| `forgeos_impact_analysis` | “what breaks if I change X?” (transitive callers + files) |
| `forgeos_paths_to` | “every path that reaches a sink” (e.g. a live-order call) |

**Ownership Intelligence (2)** — declared (rules) + observed (call graph):

| Tool | Answers |
|------|---------|
| `forgeos_runtime_owner` | domain / layer / criticality / impact + declared-vs-observed drift |
| `forgeos_runtime_summary` | ownership + consumers + dependencies |

**Data Flow Intelligence (5)** — state reads/writes + lineage:

| Tool | Answers |
|------|---------|
| `forgeos_readers` / `forgeos_writers` | who reads / writes a `<Class>.<attr>` |
| `forgeos_data_flow` | upstream (writers + callers) / downstream (readers + callers) |
| `forgeos_flow_impact` | everything a state symbol affects |
| `forgeos_lineage` | trace a path between two endpoints (e.g. Signal → Execution) |

> The Execution / Ownership / Data-Flow tools require **`forgeos sync`** (or `exec-scan`) to have
> run in the project. They're **Python-only** and deterministic — see *Code Intelligence* below.

### Set it up (one time)

```bash
uv tool install ".[mcp]"          # if not already; or from a clone: uv sync --extra mcp
which forgeos-mcp                 # copy this path (from a clone use: uv run which forgeos-mcp)
```

**Claude Code:**

```bash
claude mcp add forgeos -s user -- /ABS/PATH/TO/forgeos-mcp   # path from `which` above; -s user = all projects
claude mcp list                                              # should show forgeos ... ✓ Connected
```

Then work from the project directory so tools default to `project="."`:

```bash
cd /path/to/your/project && claude
# inside the session:  /mcp        # confirms forgeos is connected (18 tools)
```

> If your `claude` command is a profile wrapper (e.g. it tells you to use `claude-personal`
> or `claude-fictiv`), use that exact command wherever this guide says `claude`.

**Claude Desktop:** add to `~/Library/Application Support/Claude/claude_desktop_config.json`,
then fully restart the app:

```json
{ "mcpServers": { "forgeos": { "command": "/ABS/PATH/TO/forgeos-mcp", "args": [] } } }
```

Then just ask, in plain language:

> “Using forgeos, show status and run doctor.”
>
> “Using forgeos, who calls `ExecutionService.place_order`, and show every path that reaches it.”
>
> “Using forgeos, who owns `strike_state`, and what breaks if I change it?”

If you started Claude outside the project, name the path: *“… for project /path/to/project”*.

---

## Code Intelligence (Execution / Ownership / Data Flow)

Beyond the knowledge graph, ForgeOS statically analyzes your **Python** code into queryable
graphs. It is **deterministic, offline, and provider-free** — no LLM, no type inference beyond
declared annotations, no runtime tracing. Relationships it can't prove statically are counted,
never fabricated.

Build (or refresh) everything in one step:

```bash
cd /path/to/your/project
forgeos sync                # scan + compress + exec-scan + dataflow; prints a summary
```

**Keep it fresh.** The graphs reflect your **last sync** — re-run `forgeos sync` after notable
changes. To automate, install the sample git hook (refreshes after pulls/checkouts; no-ops if
forgeos isn't set up, never blocks the git op):

```bash
chmod +x scripts/forgeos-sync-hook.sh
ln -sf ../../scripts/forgeos-sync-hook.sh .git/hooks/post-merge
ln -sf ../../scripts/forgeos-sync-hook.sh .git/hooks/post-checkout
```

Two optional project config files sharpen the answers:

- **`.forgeos/ownership.yaml`** — maps code to domains/layers/criticality (governance metadata;
  declared, never inferred). Example:
  ```yaml
  rules:
    - match: { name: "^ExecutionService" }
      domain: Execution Domain
      criticality: P0
      impact: LIVE_TRADING
    - match: { path: "*/strategy/*" }
      domain: Strategy Domain
  ```
- **`.forgeos/dataflow.yaml`** — maps domain concepts to symbols so `forgeos_lineage` can trace
  named flows. Example:
  ```yaml
  anchors:
    Signal: StrategyRunner.evaluate
    Execution: ExecutionService.place_order
  ```

> **Scope:** Python only. TypeScript/JavaScript, dynamic dispatch, and runtime tracing are out
> of scope — cross-language flows (e.g. into a Next.js UI) are not covered. Coverage of
> cross-object data flow scales with how **type-annotated** the code is.

---

## Daily workflow

Three habits make ForgeOS pay off — its value compounds as you feed it:

1. **Feed** (periodic, CLI): re-`sync` after notable changes; record decisions as you go.
   ```bash
   forgeos sync
   forgeos memory add "Risk checks run before every place_order" --kind observation
   ```
2. **Use** (daily, in Claude): start a session in the project, then ask
   *“using forgeos, who calls X / what owns Y / how does Z flow / what do we know about W”*.
   Claude grounds its answers in your graphs instead of re-deriving from source each time.
3. **Promote** (periodic, CLI): turn durable lessons into skills via the human-gated loop.
   ```bash
   forgeos learn review                       # proposals awaiting a decision (nothing auto-promotes)
   forgeos learn approve <id> --actor you
   forgeos learn commit  <id> --actor you     # approved learning -> a Skill node
   ```

---

## Command reference

```bash
# workspace
forgeos init                 # create .forgeos/ in the current project
forgeos doctor               # environment + config diagnostics
forgeos status               # workspace state at a glance
forgeos wizard               # guided first-run walkthrough

# build knowledge + code intelligence
forgeos sync                 # one-shot: scan + compress + exec-scan + dataflow (or: --path <dir>)
forgeos scan                 # index the current dir into the knowledge graph (or: --path <dir>)
forgeos compress run --bulk  # build context cards
forgeos exec-scan            # build symbol/call/state graphs (Python; deterministic)

# query knowledge
forgeos memory add "<text>"  # store a memory (--scope, --kind, --ttl)
forgeos memory query         # list memory (filter with --scope / --kind)
forgeos graph query <node-id-or-label>   # `graph why <id>` explains an edge
forgeos context build <target>           # assemble a token-budgeted context bundle

# advisory (provider-backed CLI; MCP uses host reasoning instead)
forgeos mentor "<question>"   # advisory guidance (read-only; never executes)
forgeos audit                # advisory audit of current state

# human-gated learning -> skills
forgeos learn review
forgeos learn approve <id> --actor you
forgeos learn commit  <id> --actor you
forgeos skill list
forgeos skill show <id>

# providers (only needed for `forge mentor`)
forgeos provider use ollama  # select a local provider (no API key)

# portability
forgeos export <path>
forgeos import <path>
forgeos backup               # snapshot with retention pruning
```

Run `forgeos --help` (or `forgeos <group> --help`) for the full surface.

---

## Layout

```
src/forgeos/
  config/         layered configuration (defaults -> ~/.forgeos -> project/.forgeos -> env)
  observability/  structured logging with request correlation
  ports/          abstract interfaces (storage, provider, transport, tokenizer, vector)
  adapters/       concrete implementations (transport/cli, transport/mcp, storage, providers, ...)
  core/           memory, graph, repo-intel, compression, context assembly, advisory, learning,
                  exec_intel (symbols/calls), ownership_intel, dataflow_intel
  testing/        in-memory fakes + static guards for tests
docs/             architecture, implementation plan, ADRs, ROADMAP
scripts/          stdlib check + sample git hooks
tests/            unit tests + golden repository corpus
```

---

## Toolchain (for contributors)

Python 3.12 · uv · ruff · mypy (strict on `src/`) · pytest.

```bash
uv sync --extra dev --extra mcp   # create env + install (include mcp to cover the MCP adapter)
uv run ruff check .               # lint
uv run mypy                       # type-check
uv run pytest                     # tests
```

When `ruff`/`mypy` are unavailable in a constrained environment, `python scripts/check.py`
provides a stdlib-only substitute (syntax + annotation + import-hygiene checks).

---

## Troubleshooting

- **All counts are `0` / knowledge MCP tools return nothing** — the store is empty. Run
  `forgeos sync` and add a memory or two first (see *First 5 minutes*).
- **Execution / ownership / data-flow tools return nothing** — run **`forgeos sync`** (or
  `exec-scan`) in the project first; those graphs are separate from the knowledge graph.
- **`OperationalError: database is locked`** — another process holds the project's
  `.forgeos/cache/forge.sqlite` (usually a live Claude session whose `forgeos-mcp` server has it
  open). Don't run `sync`/`exec-scan` while an MCP session is using the same project. Free it:
  `pkill -f forgeos-mcp` (Claude respawns it on next use), then re-run. If a crashed run left a
  journal: `rm -f .forgeos/cache/forge.sqlite-journal .forgeos/cache/forge.sqlite-wal` (the index
  is rebuildable from snapshots).
- **`/mcp` shows fewer than 18 tools** — you're on an older build; `uv tool install ".[mcp]"`
  again and start a fresh session.
- **`scan .` errors with “unexpected extra argument”** — `scan`/`exec-scan`/`sync` take no
  positional path; use the bare command (current dir) or `--path <dir>`.
- **`doctor` shows `credentials: FAIL`** — only affects the provider-backed `forge mentor`/`audit`
  CLI. Every MCP tool works without it. To clear it: `forgeos provider use ollama` (no key), or
  ignore it. The `provider` field is the CLI's external-model setting; **MCP never uses it.**
- **`claude: command not found`, or it asks you to choose a profile** — your Claude Code is a
  profile wrapper; use the real command (e.g. `claude-personal` / `claude-fictiv`).
- **`forgeos-mcp: command not found`** — install the MCP extra: `uv tool install ".[mcp]"`.
- **`git push` returns 403 / wrong account** — with multiple GitHub accounts, ensure the active
  one can push: `gh auth switch --hostname github.com --user <you>`.
