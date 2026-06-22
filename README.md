# ForgeOS

A **local-first AI Operating System** that sits between you, your projects, and AI models.
It **preserves project knowledge while sending fewer tokens** — giving your AI assistant a
persistent memory, a knowledge graph of your codebase, compact context “cards,” and an
explainable, human-gated learning loop.

Use it two ways, together or separately:

- **CLI** (`forgeos` / `forge`) — build and query the knowledge directly in your terminal.
- **Inside Claude (MCP)** — Claude Code / Claude Desktop call ForgeOS as tools, so the
  assistant reasons with *your* accumulated project knowledge. **No API key or extra model
  required** — your Claude host is the model.

> Status: **V1.0.0**, CLI-first. Current status & roadmap: `docs/ROADMAP.md`. Architecture in
> `docs/ARCHITECTURE.md`; design decisions in `docs/adr/`; per-release changes in `CHANGELOG.md`.

---

## Requirements

- **Python 3.12+**
- **[uv](https://docs.astral.sh/uv/)** — the installer below sets it up if it's missing
- **git** — used when indexing a repository
- macOS, Linux, or Windows
- **No AI provider or API key** is needed for the CLI's core commands or for any of the
  Claude (MCP) tools. A provider (Claude API **or** a local [Ollama](https://ollama.com)) is
  only required for the provider-backed `forge mentor` CLI command — never for the MCP tools.

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
forgeos scan                     # index the current dir (files/modules/deps) into the graph
forgeos compress run --bulk      # build compact “cards” (cheap summaries of code)
forgeos memory add "We use uv + hatchling; mypy strict on src/"   # remember a fact
forgeos status                   # counts should now be non-zero
```

Query what it now knows:

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

**All seven tools are read-only and need no LLM provider** — in the MCP model your Claude host
is the reasoning model (ADR 0014):

| Tool | What it returns |
|------|-----------------|
| `forgeos_status` | project state + record counts + active provider |
| `forgeos_doctor` | environment / readiness diagnostics |
| `forgeos_skill_list` / `forgeos_skill_show` | promoted skills |
| `forgeos_graph_summary` | nodes reachable from a target in the knowledge graph |
| `forgeos_memory_summary` | stored memory records (optionally filtered) |
| `forgeos_advisory_context` | a deterministic, provider-free **grounding bundle** (cards, memory, ADRs, repo profile, decisions, findings) for the host model to reason over |

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
# inside the session:  /mcp        # confirms forgeos is connected (7 tools)
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
> “Using forgeos, get the advisory context for the memory module, then propose how to add a TTL cleanup.”
>
> “Using forgeos, what do we know about how this project handles config?”

If you started Claude outside the project, name the path: *“run forgeos_status for project /path/to/project”*.

---

## Daily workflow

Three habits make ForgeOS pay off — its value compounds as you feed it:

1. **Feed** (periodic, CLI): re-`scan` after notable changes; record decisions/gotchas as you go.
   ```bash
   forgeos scan
   forgeos memory add "Tokens cached in keychain; switch gh accounts with `gh auth switch`"
   forgeos memory add "MCP tools must return data, never print to stdout" --kind observation
   ```
2. **Use** (daily, in Claude): start a session in the project, then ask
   *“using forgeos, get advisory context for X…”*, *“what do we know about Y?”*, *“show status”*.
   Claude grounds its answers in your stored knowledge instead of re-asking you each session.
3. **Promote** (periodic, CLI): turn durable lessons into skills via the human-gated loop.
   ```bash
   forgeos learn review                       # proposals awaiting a decision (nothing auto-promotes)
   forgeos learn approve <id> --actor you
   forgeos learn commit  <id> --actor you     # approved learning -> a Skill node
   ```

**Why it helps:** persistent memory across Claude sessions (stop re-explaining your project),
grounded answers that match your codebase, and fewer tokens (cards are compact summaries, so
grounding costs less than pasting raw files).

---

## Command reference

```bash
# workspace
forgeos init                 # create .forgeos/ in the current project
forgeos doctor               # environment + config diagnostics
forgeos status               # workspace state at a glance
forgeos wizard               # guided first-run walkthrough

# build + query knowledge
forgeos scan                 # index the current dir (or: scan --path <dir>)
forgeos compress run --bulk  # build context cards
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
  core/           memory, graph, repo-intel, compression, context assembly, advisory, learning
  testing/        in-memory fakes + static guards for tests
docs/             architecture, implementation plan, ADRs, ROADMAP
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

- **All counts are `0` / MCP tools return nothing** — the store is empty. Run `forgeos scan`
  and add a memory or two first (see *First 5 minutes*).
- **`scan .` errors with “unexpected extra argument”** — `scan` takes no positional path; use
  bare `forgeos scan` (current dir) or `forgeos scan --path <dir>`.
- **`doctor` shows `credentials: FAIL`** — this only affects the provider-backed `forge mentor`
  CLI. Every MCP tool and all read-only commands work without it. To clear it, pick a local
  provider: `forgeos provider use ollama` (no API key), or just ignore it.
- **`provider` shows `claude`/`ollama` but you only use Claude Code** — that field is the CLI's
  external-model setting; the MCP tools never use it. Ignore it for the Claude workflow.
- **`claude: command not found`, or it asks you to choose a profile** — your Claude Code is a
  profile wrapper; use the real command (e.g. `claude-personal` / `claude-fictiv`) everywhere
  this guide says `claude`.
- **`/mcp` doesn't list `forgeos`** — re-run `claude mcp add forgeos -s user -- $(which forgeos-mcp)`
  and start a fresh session from the project directory.
- **`forgeos-mcp: command not found`** — install the MCP extra: `uv tool install ".[mcp]"`
  (or `uv sync --extra mcp` from a clone).
- **`git push` returns 403 / wrong account** — if you use multiple GitHub accounts, make sure
  the active one can push: `gh auth switch --hostname github.com --user <you>`.
