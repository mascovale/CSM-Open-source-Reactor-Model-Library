#!/usr/bin/env python3
"""Append user prompts and Claude responses, verbatim and timestamped, to
claude-progress/conversation-log.md.

Called by Claude Code hooks (see .claude/settings.json):
  log_conversation.py prompt    <- UserPromptSubmit (prompt text on stdin JSON)
  log_conversation.py response  <- Stop (reads the session transcript)
"""
import json
import sys
import time
from datetime import datetime
from pathlib import Path

LOG = Path(__file__).resolve().parents[2] / "claude-progress" / "conversation-log.md"


def now():
    return datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")


def append(header, body):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(f"\n---\n\n### {header} — {now()}\n\n{body.rstrip()}\n")


def is_user_prompt(entry):
    """A real typed prompt: user role, string content, not meta/tool output."""
    if entry.get("type") != "user" or entry.get("isMeta"):
        return False
    content = entry.get("message", {}).get("content")
    if isinstance(content, list):
        return any(b.get("type") == "text" for b in content) and not any(
            b.get("type") == "tool_result" for b in content
        )
    return isinstance(content, str) and not content.lstrip().startswith(
        ("<local-command", "<command-name", "<system-reminder", "<task-notification")
    )


def format_duration(seconds):
    m, s = divmod(round(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h}h {m:02d}m {s:02d}s" if h else f"{m}m {s:02d}s"


def response_text(transcript_path):
    """All assistant text since the last user prompt, and that prompt's time."""
    entries = []
    for line in Path(transcript_path).read_text(encoding="utf-8").splitlines():
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    start = max((i for i, e in enumerate(entries) if is_user_prompt(e)), default=-1)
    texts = []
    for e in entries[start + 1:]:
        if e.get("type") != "assistant" or e.get("isSidechain"):
            continue
        for block in e.get("message", {}).get("content", []):
            if block.get("type") == "text" and block.get("text", "").strip():
                texts.append(block["text"].strip())
    started = None
    if start >= 0 and entries[start].get("timestamp"):
        started = datetime.fromisoformat(entries[start]["timestamp"].replace("Z", "+00:00"))
    return "\n\n".join(texts), started


def main():
    mode = sys.argv[1]
    data = json.load(sys.stdin)
    if mode == "prompt":
        append("User prompt", data.get("prompt", ""))
    elif mode == "response":
        text, started = "", None
        # The transcript may lag the Stop event slightly; retry briefly.
        for _ in range(10):
            text, started = response_text(data["transcript_path"])
            if text:
                break
            time.sleep(0.3)
        text = text or data.get("last_assistant_message", "") or "(no text response)"
        header = "Claude response"
        if started:
            elapsed = (datetime.now().astimezone() - started).total_seconds()
            header += f" (execution time: {format_duration(elapsed)})"
        append(header, text)


if __name__ == "__main__":
    main()
