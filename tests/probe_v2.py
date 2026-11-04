"""Phase-0 gate probe (v2).

For each configured entrypoint, using the official MCP client over stdio:
  1. initialize (records protocol version + server name)
  2. tools/list
  3. configured positive tools/call(s) -> MUST succeed
  4. a negative call to a nonexistent tool -> MUST come back isError=true

Server stderr goes to tests/logs/<label>.log. Exception groups are unwrapped.
Usage: python tests/probe_v2.py [--protocol-only] [label ...]
Protocol-only mode skips configured primary calls, runs curated local
read-only calls, and avoids live upstream access.
Exits non-zero unless every probed server reports OK.
"""
import asyncio
import json
import os
import sys
import time
from collections import Counter
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parent.parent
PY = os.environ.get("PROBE_PY", sys.executable)
HERE = Path(__file__).resolve().parent
LOGS = HERE / "logs"
LOGS.mkdir(exist_ok=True)

TARGETS = {
    "goliath":    ("goliath/server.py",          "goliath_get_swarm_state", {}),
    "ids":        ("ids/server_ai_enhanced.py",  "ai_semantic_search", {"query": "Candidate A astronomy data", "max_results": 3}),
    "eds":        ("eds/server_enhanced.py",     "assess_content_quality_enhanced", {"content": "Candidate A requires a preregistered public-data test.", "topic": "candidate testing"}),
    "ipa":        ("ipa/server_ultimate.py",     "ipa_research_capabilities", {}),
    "vrgc":       ("vrgc/server_enhanced.py",    "vrgc_assess_system", {}),
    "dpa":        ("dpa/server.py",              "get_intent", {"text": "analyze candidate astronomy test gate"}),
    "web-search": ("web-search/server.py",       "get_search_suggestions", {"query": "mcp"}),
    "loc":        ("loc/server.py",              "loc_search_catalog", {"query": "astronomy", "limit": 1}),
    "science-data": ("science_data/server.py",   "science_data_list_sources", {"domain": "astronomy"}),
}
EXPECTED_TOOL_NAMES = {
    "goliath": {"goliath_get_swarm_state"},
    "ids": {
        "ai_semantic_search",
        "knowledge_graph_query",
        "conversational_documentation",
        "ai_document_analysis",
        "ids_trace_lineage",
    },
    "vrgc": {
        "vrgc_self_heal_code",
        "vrgc_web_fetch",
        "vrgc_web_search",
        "vrgc_download_file",
        "vrgc_ftp_access",
        "vrgc_api_request",
        "vrgc_assess_system",
        "vrgc_monitor_training",
        "vrgc_optimize_hardware",
        "vrgc_verify_covenant",
    },
}
SAFE_READ_ONLY_CALLS = {
    "ids": [
        ("knowledge_graph_query", {"query_type": "find_related", "concept": "Candidate A", "depth": 1}),
        ("conversational_documentation", {"question": "Where are Candidate A test contracts documented?"}),
        ("ai_document_analysis", {
            "analysis_scope": "single_file",
            # Ships with this repo, so the call is valid in a standalone checkout too.
            "target_path": str(ROOT / "README.md"),
            "include_quality_metrics": False,
        }),
        ("ids_trace_lineage", {"entity": "Candidate A"}),
    ],
    "eds": [
        ("verify_sacred_covenant_compliance", {
            "content_source": "public scientific metadata",
            "license_info": "not established; review required",
            "intended_use": "research",
        }),
    ],
    "ipa": [
        ("ipa_research_history", {"limit": 1}),
    ],
    "vrgc": [
        ("vrgc_monitor_training", {}),
        ("vrgc_optimize_hardware", {}),
        ("vrgc_verify_covenant", {}),
    ],
    "dpa": [
        ("analyze", {"text": "Assess the current Candidate A evidence gate."}),
        ("get_entities", {"text": "Candidate A data test in November 2026"}),
        ("get_accessibility_integration_status", {}),
    ],
    "web-search": [
        ("get_search_suggestions", {"query": "physics Candidate A public data research"}),
    ],
}
DENIED_TOOL_CALLS = {
    "dpa": [
        ("ids_update", {}),
        ("ids_tag", {}),
        ("ids_sync", {}),
        ("ids_generate_docs", {}),
    ],
    "goliath": [
        ("goliath_synergize_memory", {"key": "probe", "value": {"test": True}}),
        ("eds_scrape_mit_ocw", {"topic": "probe"}),
    ],
    "ids": [
        ("neural_forge_integration", {"integration_type": "training_status"}),
    ],
    "vrgc": [
        ("vrgc_download_file", {"url": "https://example.org/probe.dat"}),
        ("vrgc_ftp_access", {"server": "example.org", "operation": "upload", "path": "/probe"}),
    ],
}

def is_error_result(is_error, text):
    if is_error:
        return True
    try:
        payload = json.loads(text)
    except (TypeError, json.JSONDecodeError):
        return False
    return isinstance(payload, dict) and (
        payload.get("status") == "error" or "error" in payload
    )


def validate_tool_catalog(tools, expected_names=None):
    names = [tool.name for tool in tools]
    duplicate_names = sorted(name for name, count in Counter(names).items() if count > 1)
    invalid_schemas = []
    for tool in tools:
        schema = tool.inputSchema
        if not isinstance(schema, dict) or schema.get("type") != "object":
            invalid_schemas.append(tool.name)
            continue
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        if (
            not isinstance(properties, dict)
            or not isinstance(required, list)
            or not set(required).issubset(properties)
        ):
            invalid_schemas.append(tool.name)

    expected_mismatch = (
        expected_names is not None and set(names) != set(expected_names)
    )
    return {
        "valid": not duplicate_names and not invalid_schemas and not expected_mismatch,
        "duplicate_names": duplicate_names,
        "invalid_schemas": invalid_schemas,
        "unexpected_names": (
            sorted(set(names) - set(expected_names))
            if expected_names is not None else []
        ),
        "missing_names": (
            sorted(set(expected_names) - set(names))
            if expected_names is not None else []
        ),
    }


def build_tool_coverage(tool_names, call_results=None, positive_ok=False):
    if isinstance(call_results, dict):
        results = call_results
    elif call_results is not None:
        results = {call_results: positive_ok}
    else:
        results = {}
    return [
        {
            "tool": name,
            "status": (
                "positive_smoke_passed"
                if results.get(name) is True
                else "positive_smoke_failed"
                if name in results
                else "not_individually_exercised"
            ),
        }
        for name in tool_names
    ]


def flatten(e):
    if isinstance(e, BaseExceptionGroup):
        out = []
        for sub in e.exceptions:
            out.extend(flatten(sub))
        return out
    return [e]


async def probe(label, script, tool, args, timeout=90, protocol_only=False):
    rec = {
        "server": label,
        "script": script,
        "mode": "protocol-only" if protocol_only else "smoke",
    }
    target_path = ROOT / script
    params = StdioServerParameters(
        command=PY,
        args=[str(target_path)],
        cwd=str(target_path.parent),
        env={
            **os.environ,
            "PYTHONIOENCODING": "utf-8",
            "PYTHONUTF8": "1",
            "MCP_WORKSPACE_ROOT": str(ROOT.parent),
            "MCP_CACHE_DIR": str(ROOT / ".cache"),
            "MCP_ALLOW_MUTATIONS": "0",
        },
    )
    t0 = time.time()
    errlog = open(LOGS / f"{label}.log", "w", encoding="utf-8", errors="replace")
    try:
        async with asyncio.timeout(timeout):
            async with stdio_client(params, errlog=errlog) as (r, w):
                async with ClientSession(r, w) as s:
                    init = await s.initialize()
                    rec["init_s"] = round(time.time() - t0, 2)
                    rec["protocol"] = init.protocolVersion
                    rec["server_name"] = init.serverInfo.name
                    tl = await s.list_tools()
                    rec["tools"] = len(tl.tools)
                    rec["tool_names"] = [t.name for t in tl.tools]
                    catalog_check = validate_tool_catalog(
                        tl.tools,
                        expected_names=EXPECTED_TOOL_NAMES.get(label),
                    )
                    rec["tool_catalog_ok"] = catalog_check["valid"]
                    if not catalog_check["valid"]:
                        rec["tool_catalog_errors"] = catalog_check
                    run_positive = tool and (not protocol_only or label == "goliath")
                    if run_positive:
                        res = await s.call_tool(tool, args)
                        txt = " ".join(getattr(c, "text", "") for c in res.content)
                        rec["call"] = tool
                        rec["call_isError"] = res.isError
                        rec["call_excerpt"] = txt[:240].replace("\n", " ")
                        rec["positive_call_ok"] = not is_error_result(res.isError, txt)
                    for safe_tool, safe_args in SAFE_READ_ONLY_CALLS.get(label, []):
                        safe_result = await s.call_tool(safe_tool, safe_args)
                        safe_text = " ".join(
                            getattr(content, "text", "") for content in safe_result.content
                        )
                        safe_ok = not is_error_result(safe_result.isError, safe_text)
                        if label == "ids" and safe_tool == "ai_document_analysis":
                            safe_ok = safe_ok and "Total files analyzed: 1" in safe_text
                        rec.setdefault("additional_calls", {})[safe_tool] = {
                            "ok": safe_ok,
                            "isError": safe_result.isError,
                            "excerpt": safe_text[:180].replace("\n", " "),
                        }
                    neg = await s.call_tool("__nonexistent_tool__", {})
                    rec["negative_isError"] = neg.isError
                    for denied_tool, denied_args in DENIED_TOOL_CALLS.get(label, []):
                        denied = await s.call_tool(denied_tool, denied_args)
                        rec.setdefault("denied_calls", {})[denied_tool] = denied.isError
                    if not neg.isError:
                        rec["status"] = "FALSE_SUCCESS"
                    elif "positive_call_ok" in rec and not rec["positive_call_ok"]:
                        rec["status"] = "POSITIVE_CALL_FAILED"
                    elif any(
                        not call["ok"]
                        for call in rec.get("additional_calls", {}).values()
                    ):
                        rec["status"] = "ADDITIONAL_CALL_FAILED"
                    elif not rec["tool_catalog_ok"]:
                        rec["status"] = "TOOL_CATALOG_FAILED"
                    elif any(not failed for failed in rec.get("denied_calls", {}).values()):
                        rec["status"] = "DENIED_TOOL_CALL_SUCCEEDED"
                    else:
                        rec["status"] = "OK"
                    rec["tool_coverage"] = build_tool_coverage(
                        rec["tool_names"],
                        {
                            name: call["ok"]
                            for name, call in rec.get("additional_calls", {}).items()
                        } | (
                            {rec["call"]: rec["positive_call_ok"]}
                            if "positive_call_ok" in rec else {}
                        ),
                    )
    except BaseException as e:  # noqa: BLE001 - probe must record everything
        subs = flatten(e)
        rec["status"] = "FAIL"
        rec["error"] = " | ".join(f"{type(x).__name__}: {str(x)[:200]}" for x in subs)
    finally:
        errlog.close()
    rec["elapsed_s"] = round(time.time() - t0, 2)
    return rec


def gate_exit_code(results):
    """Return 0 only when at least one server was probed and every one is OK."""
    return 0 if results and all(r.get("status") == "OK" for r in results) else 1


async def main():
    protocol_only = "--protocol-only" in sys.argv[1:]
    labels = [arg for arg in sys.argv[1:] if arg != "--protocol-only"] or list(TARGETS)
    results = []
    for label in labels:
        script, tool, args = TARGETS[label]
        r = await probe(label, script, tool, args, protocol_only=protocol_only)
        results.append(r)
        print(json.dumps({k: v for k, v in r.items() if k != "tool_names"}), flush=True)
    (HERE / "probe_v2_results.json").write_text(json.dumps(results, indent=2))
    ok = sum(r["status"] == "OK" for r in results)
    print(f"GATE: {ok}/{len(results)} OK")
    return gate_exit_code(results)


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
