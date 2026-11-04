# SpaceEntropyCompression MCP integration

This submodule is integrated as a standalone-first project tool pack. The
workspace configuration is maintained in `.vscode/mcp.json`; it launches the
local IDS, EDS, IPA, VRGC, DPA, web-search, LoC, science-data, and Goliath
servers. Goliath currently exposes only its tested read-only swarm/hardware
status operation. Its legacy EDS, IPA, VRGC, web-search, IDS, DPA, and
chronology bridge routes are not registered until they have real dispatch,
error propagation, and safety tests. Use each verified standalone server for
those tools.

## Workspace and local setup

The client passes `MCP_WORKSPACE_ROOT` and `MCP_CACHE_DIR` using workspace
variables. Servers must not infer the SpaceEntropyCompression root from the
MCP server's own directory or from a machine-specific path. If an explicit
workspace root is missing or invalid, startup must fail rather than silently
index another directory. Goliath writes its logs under
`MCP_CACHE_DIR/goliath_logs` (default `.mcp/.cache/goliath_logs`), never into
the workspace root.

Install the declared MCP dependencies in the selected Python environment before
launching the servers. The workspace VS Code profile uses `py -3.12`; adjust
the interpreter selector only as a workspace-local change when necessary.
DPA's intent processor and VRGC's hardware diagnostics run in CPU/minimal
installations when optional PyTorch or GPUtil packages are absent; accelerator
metrics are reported unavailable rather than preventing server startup.

## Science-data coverage (initial adapters)

The `science_data` server exposes:

- `science_data_list_sources`: source registry with implemented status and
  coverage limits.
- `science_data_query_exoplanets`: bounded read-only TAP query to NASA
  Exoplanet Archive using a fixed table and allowlisted columns.
- `science_data_search_inspire`: bounded search of public INSPIRE-HEP
  literature metadata.

Both query tools return the source URL, query, UTC retrieval time, SHA-256 of
the raw response, and an evidence-class label. They do not download data to
disk and accept no arbitrary URLs. Other astronomy and HEP/quantum archives
are catalogued as planned, not represented as working adapters.

## Safety and evidence limits

- VRGC downloads, FTP, sandbox execution, and mutating API calls, and DPA's
  `ids_update`, `ids_tag`, `ids_sync`, and `ids_generate_docs`, require both an
  explicit per-call `approved: true` (the literal boolean) and
  `MCP_ALLOW_MUTATIONS=1`. The shared check lives in
  [`../shared/mutation_gate.py`](../shared/mutation_gate.py). This is a local
  two-part check, not an authorization system.
- DPA's IDS bridge is disabled by default. It runs an external script only when
  `DPA_IDS_API_PATH` is an absolute path to an existing file, and it never
  executes a script it finds in the host repository. The script runs with a
  60-second timeout and without access to the MCP protocol stream.
- IDS knowledge-graph caches are versioned JSON under `ids/.cache/` and are never
  unpickled; any older `*.pkl` cache is ignored and the graph is rebuilt.
- Retrieved pages and records are untrusted data, not agent instructions.
- Public access does not imply redistribution or model-training rights; retain
  item-level licensing and citation checks for future data retrieval.
- Archive release state, proprietary access, API limits, schemas, and rights
  differ. This pack does not promise complete coverage of all observable data
  or telescope imagery.
- An API response, software test, or literature result is not physical
  confirmation of either EMRF candidate.

## Verification

From the SpaceEntropyCompression repository root, run the focused unit suite
and protocol probe with:

```powershell
py -3.12 -m unittest discover -s .mcp\tests -p "test_*.py"
py -3.12 .mcp\tests\probe_v2.py
```

The latest verification passed 43 focused unit tests and the full bounded
smoke probe passed all nine configured MCP targets. The probe exits non-zero
unless every target reports OK. It individually exercised
21 of 63 listed tools; the other 42 are explicitly marked
`not_individually_exercised` in
[`../tests/probe_v2_results.json`](../tests/probe_v2_results.json). The probe
checks initialization, unique tool names, object-shaped input schemas,
positive tool calls, unknown-tool errors, Goliath's rejection of unregistered
mutation/placeholder routes, and that the guarded VRGC, DPA, and Goliath tools
are denied while `MCP_ALLOW_MUTATIONS=0`. Protocol-only mode uses curated
local read-only calls and avoids external API calls, so it is suitable for CI.
The unit suite and protocol-only probe were also run from a clean checkout in a
virtual environment built only from `requirements.txt` and passed; the two
workspace-profile checks in `test_project_config.py` skip there because they
need the host project's `.vscode/mcp.json`. On 2026-11-04, the GitHub Actions
workflow ([`../.github/workflows/ci.yml`](../.github/workflows/ci.yml)) passed
all four Ubuntu/Windows and Python 3.11/3.12 jobs (run `41829273692`). Its
first run exposed a Windows output-decoding failure in the fresh-start test
harness; the harness now decodes subprocess output explicitly as UTF-8. Ubuntu
has not been exercised locally.
Bounded NASA Exoplanet Archive and INSPIRE-HEP queries previously returned
three records with query provenance and SHA-256. These are startup/schema/
smoke checks, not proof that every operation of every standalone server works.
Before promoting an individual tool, add deterministic success, validation,
failure, and permission tests; network-facing behavior must use mocked
upstreams in CI.
