#!/usr/bin/env python3
"""
!/usr/bin/env python3

**Created:** October-15-2024  
**Updated:** August-04-2025  
**Author:** ImpressionCore Team  
**Tags:** #dpa/ids_bridge.py #api #python #source_code  
**Category:** Source Code  
**Status:** Active
"""





import os
import subprocess
import sys
from pathlib import Path

IDS_API_ENV = "DPA_IDS_API_PATH"
COMMAND_TIMEOUT_SECONDS = 60


class IDSBridge:
    """Bridge for DPA to control IDS server operations.

    The bridge is disabled unless DPA_IDS_API_PATH names an absolute path to an
    existing IDS API script. It never searches the host repository for a script
    to execute.
    """
    def __init__(self, ids_api_path=None):
        configured = ids_api_path if ids_api_path is not None else os.environ.get(IDS_API_ENV, "")
        self.ids_api_path = str(configured).strip()

    def update(self):
        return self._run_cmd(['update'])

    def tag(self):
        return self._run_cmd(['tag'])

    def sync(self):
        return self._run_cmd(['sync'])

    def status(self):
        return self._run_cmd(['status'])

    def search(self, query):
        return self._run_cmd(['search', query])

    def generate_docs(self):
        return self._run_cmd(['generate-docs'])

    def _run_cmd(self, args):
        if not self.ids_api_path:
            return {
                "error": "ids_bridge_disabled",
                "message": f"Set {IDS_API_ENV} to an absolute IDS API script path to enable the bridge (standalone mode).",
            }
        script = Path(self.ids_api_path)
        if not script.is_absolute() or not script.is_file():
            return {
                "error": "ids_bridge_script_invalid",
                "message": f"{IDS_API_ENV} must be an absolute path to an existing file.",
            }
        cmd = [sys.executable, str(script)] + args
        try:
            result = subprocess.run(
                cmd,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                check=True,
                timeout=COMMAND_TIMEOUT_SECONDS,
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            return {"error": "ids_bridge_command_failed", "message": (e.stderr or "").strip()}
        except Exception as e:
            return {"error": "ids_bridge_error", "message": str(e)}
