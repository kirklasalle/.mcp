# Changelog

All notable changes to the `.mcp` Model Context Protocol Enterprise Tooling Fleet will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- **`science_data` server**: bounded, read-only NASA Exoplanet Archive (fixed TAP table, allowlisted columns) and INSPIRE-HEP literature adapters. Each result carries the source URL, query, UTC retrieval time, response SHA-256 and an evidence-class label; arbitrary URLs are rejected and nothing is written to disk.
- **`shared/workspace.py` and `shared/network_safety.py`**: explicit workspace-root resolution via `MCP_WORKSPACE_ROOT` (startup fails on a missing or invalid root) and helpers for bounded outbound requests.
- **Mutation gate**: one shared check (`shared/mutation_gate.py`) now guards VRGC `vrgc_download_file`, `vrgc_ftp_access`, `vrgc_sandbox_execute`, `vrgc_war_game_refactor` (the last two are unimplemented and not listed) and `vrgc_api_request` with a method other than GET/HEAD/OPTIONS, plus DPA `ids_update`, `ids_tag`, `ids_sync` and `ids_generate_docs`. These calls are denied unless `MCP_ALLOW_MUTATIONS=1` is set and the call passes `approved=true` (the literal boolean; `"true"` or `1` is rejected).
- **Verification**: 43 unit/configuration tests, per-tool coverage reporting in `tests/probe_v2.py`, a `--protocol-only` probe mode that makes no upstream calls, and a CI workflow (Ubuntu and Windows, Python 3.11 and 3.12) using SHA-pinned actions. The latest bounded smoke probe passed 9/9 server targets and individually exercised 21 of 63 listed tools; the remaining 42 are marked `not_individually_exercised`. Denied-call checks (including the four DPA mutation tools) are recorded separately and do not count toward that figure. The unit suite and the protocol-only probe also pass from a clean checkout in a virtual environment built only from `requirements.txt`; the two profile checks in `test_project_config.py` are skipped there because they need the host workspace's `.vscode/mcp.json`. The first GitHub Actions run found a Windows output-decoding failure in the fresh-start test harness; after the explicit UTF-8 fix, all four Ubuntu/Windows and Python 3.11/3.12 jobs passed (run `41829273692`).
- **`docs/SPACE_ENTROPY_COMPRESSION.md`**: project integration guide with verification scope and limitations.

### Changed
- **Goliath** exposes only the tested read-only `goliath_get_swarm_state`; unverified bridge routes are not registered and unavailable GPU telemetry is reported as unknown rather than simulated. Logs now default to `MCP_CACHE_DIR/goliath_logs` (previously `.goliath_logs/` in the working directory, which polluted the host project).
- **IDS**: `ai_document_analysis` honors `single_file` scope, `ids_trace_lineage` returns an empty result for unknown entities, and `server_ai_enhanced.py` (workspace-root aware) is the supported entry point. Knowledge-graph caches (`ids/.cache/knowledge_graph.json` and `ids_knowledge_graph.json`) are now versioned JSON written atomically; they were pickles, which run arbitrary code when a tampered cache is loaded. Existing `*.pkl` caches are never read and the graphs are rebuilt.
- **VRGC**: `vrgc_verify_covenant` is a read-only integrity check; it previously called file-protection routines that created backups and changed permissions.
- **Startup resilience**: DPA starts without PyTorch and VRGC without GPUtil; LoC upstream failures now raise tool errors (`loc_*_upstream_failure`). DPA's accessibility status route uses the `AccessibilityIntegration` wrapper.
- **DPA IDS bridge**: disabled unless `DPA_IDS_API_PATH` names an absolute path to an existing script. It previously derived `<repo root>/src/core/utils/ids_server_api.py` from its own location, which with `.mcp` as a submodule is the host repository, so any script appearing at that path would have been executed; a missing script was also reported as a successful result. Failures are now error results (`ids_bridge_disabled`, `ids_bridge_script_invalid`, `ids_bridge_command_failed`, `ids_bridge_error`), the child runs with a 60-second timeout, and its stdin is detached from the MCP protocol stream (on Windows an inherited stdin pipe stalled the child until the timeout).
- **Client configuration**: `mcp-settings.json` uses workspace-relative `py -3.12` launches instead of machine-specific absolute paths; `antigravity_mcp_config.json`, `claude_desktop_config.json` and `nexus-mcp-settings.json` no longer ship stale server entries.
- **Documentation**: historical capability and verification claims in the README, IDS and VRGC guides are marked unverified.

### Removed
- IDS `neural_forge_integration`, which returned hard-coded mock training and GPU figures (default model `impressioncore-b1`) rather than real telemetry.
- VRGC tools without a real implementation are no longer listed (`UNIMPLEMENTED_TOOL_NAMES` in `vrgc/server_enhanced.py`).

### Fixed
- **IDS startup crash on a fresh checkout**: `server_ai_enhanced.py` raised `NameError: name 'nx' is not defined` when no graph cache existed and `numpy` was not installed, because `networkx` was imported inside the optional AI-library guard. A leftover `knowledge_graph.pkl` hid it wherever the server had already run. `networkx` is now imported unconditionally (it is a hard dependency of `graph_bridge`), and `tests/test_ids_fresh_start.py` starts the server with an empty cache and `numpy` blocked.
- **Probe exit status**: `tests/probe_v2.py` always exited 0, so the CI probe step could not fail. It now exits 1 unless every probed server reports OK (`gate_exit_code`). Its IDS single-file analysis targets this repository's `README.md` instead of the host project's `STATUS.md`, so the probe is valid in a standalone checkout.
- **Windows fresh-start regression harness**: decode captured IDS subprocess output explicitly as UTF-8 with replacement, avoiding failures when Unicode diagnostics are emitted on Windows runners using a legacy console code page.

---

## [2.0.0] - 2026-10-23

### Comprehensive Fleet Audit & Phase 0 Stabilization Release

This major release consolidates the fleet under a single, unified repository layout (`dpa`, `eds`, `goliath`, `ids`, `ipa`, `loc`, `vrgc`, `web-search`), establishes strict protocol compliance with the Model Context Protocol (MCP) date-versioned standard (`2025-11-25`), and introduces robust protocol-isolation infrastructure.

### Added
- **`LICENSE`**: Official Apache License, Version 2.0 ensuring enterprise protection and open-source adoption.
- **`pyproject.toml` & `requirements.txt`**: Unified PEP 517/621 packaging standard supporting 1-command `pip install -e .` and `uv` workspace resolution.
- **`scripts/configure_clients.py`**: Automated dynamic client configuration generator auto-detecting fleet root, Python executable, and host OS with `--install` support.
- **`.github/workflows/ci.yml`**: Multi-OS automated GitHub Actions CI/CD matrix verifying protocol gate (8/8 OK) on Ubuntu, Windows, and macOS.
- **Public Product Website (`D:\Projects\Websites\.mcp`)**: Interactive developer portal and command center featuring live telemetry, server explorer, terminal sandbox, and Chart.js competitive radar.
- **`shared/stdio_guard.py`**: Protocol-safe stdio stream isolation. Duplicates file descriptor 1 and redirects Python/C-level `stdout` to `stderr`, completely eliminating JSON-RPC protocol corruption caused by stray prints, banners, and progress bars.
- **`shared/sdk_adapter.py`**: Unified SDK wrapper providing consistent server instantiation, exception mapping to `isError=True` payloads, and JSON-RPC message serialization across both `FastMCP` and low-level `Server` implementations.
- **Automated Probe Suite (`tests/probe_v2.py`)**: Protocol and functional verification harness executing `initialize`, `tools/list`, positive tool execution, and negative tool handling (`isError=True`) against live servers.
- **1-Click Client Configurations**: Pre-validated JSON configurations for Google Antigravity IDE (`antigravity_mcp_config.json`), Anthropic Claude Desktop (`claude_desktop_config.json`), Cursor/Windsurf (`mcp-settings.json`), and Nexus (`nexus-mcp-settings.json`).
- **Comprehensive Documentation Suite**:
  - `docs/PRD.md`: Formal Product Requirements Document defining product architecture, functional specifications, and market positioning.
  - `docs/MARKET_RESEARCH.md`: Global 2026 MCP ecosystem analysis, competitive benchmarking, moats, and financial TAM models.
  - `docs/WEBSITE_REQUIREMENTS_AUDIT.md`: Complete audit and specification for the public digital presence.
  - `docs/USER_GUIDE.md`: End-user installation, 1-click IDE configuration, and tool workflow reference.
  - `docs/DEVELOPER_GUIDE.md`: Architecture manual, stdio stream safety, tool creation patterns, and testing guidelines.
  - `assets/images/`: Visual assets including repo hero banner, architecture schematic, user workflow diagram, and secure tool execution lifecycle.

### Changed
- **Directory Normalization**: Migrated legacy directory names to canonical micro-server packages (`impressioncore-dpa` → `dpa`, `impressioncore-eds` → `eds`, `impressioncore-goliath` → `goliath`, `ids-mcp` → `ids`, `impressioncore-ipa` → `ipa`, `loc-mcp-server` → `loc`, `impressioncore-vrgc` → `vrgc`, `web-search-mcp` → `web-search`).
- **Protocol Version Negotiation**: Updated server capability negotiation to target MCP `2025-11-25`.
- **DPA Server (`dpa/server.py`)**: Restructured NLU fallback chain to eliminate `TypeError: 'NoneType' object is not callable` in `get_intent` and resolved import pathing.
- **IPA Server (`ipa/server_ultimate.py`)**: Integrated `shared.stdio_guard` and fixed `FLEET_ROOT` path resolution, enabling `ipa_research_capabilities` and arXiv search tools to execute reliably without `ModuleNotFoundError`.
- **Goliath Orchestrator (`goliath/server.py`)**: Corrected tool bridge dispatch method call from `find_tool_bridge` to `get_tool_bridge`.
- **Documentation Audit**: Aligned `README.md` and `shared/MCP_ARCHITECTURE_DOCUMENTATION.md` with true operational state, eliminating misleading operational claims and labeling work-in-progress components with `[CURRENT STATE]`.

### Fixed
- Fixed 25 `SyntaxWarning` occurrences in docstrings caused by unescaped `\i` tags.
- Fixed JSON-RPC stream breakage across `eds`, `ipa`, and `vrgc` caused by startup ASCII art and logging to stdout.
- Fixed false-success bug where tool execution failures and non-existent tool requests returned `isError: false`. All servers now strictly adhere to standard JSON-RPC error protocols and `isError: true`.

---

## [1.5.0] - 2026-09-29

### Multi-Server Registry & Cross-Server Bridges
- Added Goliath master orchestrator multiplexing child servers via internal bridge modules.
- Introduced persistent swarm memory blackboard (`goliath_swarm_memory.json`).
- Integrated Library of Congress (`loc`) research server for catalog, newspaper, and legislative archives.
- Implemented DuckDuckGo and Google search fallback cascades in `web-search`.

---

## [1.0.0] - 2025-08-04

### Initial Prototype Monorepo
- Initial implementation of specialized micro-servers: `dpa`, `eds`, `ids`, `ipa`, and `vrgc`.
- Basic JSON-RPC 2.0 stdio server loops.
- Preliminary integration with Kirk LaSalle's Agentic Sacred Covenant and Prime Directive.
