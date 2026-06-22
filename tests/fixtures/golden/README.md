# Golden Repository Test Corpus

Fixed, version-controlled sample repositories used for regression testing across
**RepoIntel**, the **Knowledge Graph**, **Compression**, and **Context Assembly**.

| Corpus     | Shape                                              | Exercises |
|------------|----------------------------------------------------|-----------|
| `small`    | one package, internal imports                      | basic scan + dep edges |
| `medium`   | two packages, cross-imports, one external dep      | internal vs external deps |
| `monorepo` | two services + shared lib                           | multi-root module discovery |

`MANIFEST.yaml` records expected counts (modules, internal edges, external deps).
Each engine asserts its output against these as it is implemented. Load via
`tests.fixtures.golden_loader` (`golden_root`, `corpus_path`, `load_manifest`).

**Do not** add provider calls or network access to corpus tests — RepoIntel must
remain deterministic and provider-free (ADR 0005).
