#!/usr/bin/env python3
"""Minimal MCP stdio client for the KiCAD-MCP-Server (JSON-RPC 2.0)."""
import json, os, subprocess, sys

ROOT = "/Users/dblab/Development/projects/kicad"
SERVER = f"{ROOT}/vendor/KiCAD-MCP-Server"
PYTHON = f"{ROOT}/.venv-kicad-mcp/bin/python"


class MCP:
    def __init__(self):
        env = dict(os.environ)
        env["KICAD_PYTHON"] = PYTHON
        env["PYTHONPATH"] = f"{ROOT}/.venv-kicad-mcp/lib/python3.9/site-packages"
        self.p = subprocess.Popen(
            ["node", "dist/index.js"], cwd=SERVER, env=env,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True, bufsize=1)
        self.id = 0
        self._send("initialize", {
            "protocolVersion": "2025-06-18", "capabilities": {},
            "clientInfo": {"name": "kicad-build", "version": "1"}})
        self._send_notification("notifications/initialized", {})

    def _send(self, method, params):
        self.id += 1
        msg = {"jsonrpc": "2.0", "id": self.id, "method": method, "params": params}
        self.p.stdin.write(json.dumps(msg) + "\n"); self.p.stdin.flush()
        return self._wait(self.id)

    def _send_notification(self, method, params):
        self.p.stdin.write(json.dumps({"jsonrpc": "2.0", "method": method, "params": params}) + "\n")
        self.p.stdin.flush()

    def _wait(self, want_id):
        while True:
            line = self.p.stdout.readline()
            if not line:
                err = self.p.stderr.read(4000)
                raise RuntimeError("MCP server died:\n" + err[-3000:])
            line = line.strip()
            if not line or not line.startswith("{"):
                continue
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue
            if msg.get("id") == want_id:
                if "error" in msg:
                    raise RuntimeError(msg["error"])
                return msg.get("result", {})

    def call(self, tool, args=None):
        res = self._send("tools/call", {"name": tool, "arguments": args or {}})
        if res.get("isError"):
            raise RuntimeError(f"{tool}: {res}")
        content = res.get("content") or []
        if content and content[0].get("type") == "text":
            try:
                return json.loads(content[0]["text"])
            except json.JSONDecodeError:
                return content[0]["text"]
        return res

    def close(self):
        try:
            self.p.terminate()
        except Exception:
            pass


if __name__ == "__main__":
    m = MCP()
    print(m.call("check_kicad_ui"))
    m.close()
