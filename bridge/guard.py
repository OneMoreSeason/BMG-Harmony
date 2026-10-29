"""PreToolUse boundary for delegated Claude file tools; no shell or MCP tools."""
import json
import sys
from pathlib import Path

FILE_TOOLS = {"Read": "file_path", "Write": "file_path", "Edit": "file_path",
              "Glob": "path", "Grep": "path"}


def check(policy, event):
    name = event.get("tool_name", "")
    if name not in FILE_TOOLS:
        return False, "Tool is not part of this delegation."
    root = Path(policy["workdir"]).resolve()
    value = event.get("tool_input", {}).get(FILE_TOOLS[name]) or str(root)
    try:
        path = Path(value)
        if not path.is_absolute():
            path = root / path
        path = path.resolve()
        relative = path.relative_to(root)
    except (ValueError, OSError, RuntimeError):
        return False, "Path is outside the assigned workspace."
    if any(p.lower() in {".git", ".claude", ".codex", ".agents", ".mcp.json"}
           for p in relative.parts):
        return False, "Agent-control and Git metadata paths are not task files."
    if name in {"Write", "Edit"}:
        allowed = {(root / p).resolve() for p in policy.get("allowed_files", [])}
        if policy["mode"] != "implement" or path not in allowed:
            return False, "Write is outside this task's explicit allowed_files."
    return True, ""


def main():
    try:
        policy = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
        event = json.load(sys.stdin)
        ok, reason = check(policy, event)
    except Exception:
        ok, reason = False, "Delegation boundary could not be validated."
    if not ok:
        print(reason, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
