#!/usr/bin/env python3
"""Append user prompts and Claude responses, verbatim and timestamped, to
claude-progress/conversation-log.md.

Called by Claude Code hooks (see .claude/settings.json):
  log_conversation.py prompt    <- UserPromptSubmit (prompt text on stdin JSON)
  log_conversation.py response  <- Stop (reads the session transcript)
  log_conversation.py commands  <- SessionEnd (flushes pending slash commands)

Local slash commands listed in LOGGED_COMMANDS (e.g. /effort) never reach the
model, so they are picked up from the transcript on every hook call and
logged once each, keyed by their transcript uuid.
"""
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

LOG = Path(__file__).resolve().parents[2] / "claude-progress" / "conversation-log.md"
LOGGED_COMMANDS = {"/effort"}


def now():
    return datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")


def append(header, body, stamp=None, marker=""):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(f"\n---\n\n### {header} — {stamp or now()}\n{marker}\n{body.rstrip()}\n")


def read_transcript(transcript_path):
    entries = []
    for line in Path(transcript_path).read_text(encoding="utf-8").splitlines():
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return entries


def tag(name, text):
    m = re.search(rf"<{name}>(.*?)</{name}>", text, re.S)
    return m.group(1).strip() if m else ""


def log_commands(transcript_path):
    """Log LOGGED_COMMANDS slash commands (with their output) not yet in the log."""
    entries = read_transcript(transcript_path)
    logged = LOG.read_text(encoding="utf-8") if LOG.exists() else ""
    for i, e in enumerate(entries):
        content = e.get("message", {}).get("content")
        if e.get("type") != "user" or not isinstance(content, str):
            continue
        name = tag("command-name", content)
        if name not in LOGGED_COMMANDS or f"<!-- cmd:{e.get('uuid')} -->" in logged:
            continue
        line = f"{name} {tag('command-args', content)}".strip()
        output = next(
            (tag("local-command-stdout", c.get("message", {}).get("content", ""))
             for c in entries[i + 1:]
             if c.get("parentUuid") == e.get("uuid")
             and isinstance(c.get("message", {}).get("content"), str)),
            "",
        )
        stamp = datetime.fromisoformat(e["timestamp"].replace("Z", "+00:00")).astimezone()
        append(f"Slash command `{name}`",
               f"```\n{line}\n```\n\nOutput: {output}" if output else f"```\n{line}\n```",
               stamp=stamp.strftime("%Y-%m-%d %H:%M:%S %Z"),
               marker=f"<!-- cmd:{e.get('uuid')} -->\n")


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
    entries = read_transcript(transcript_path)
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
    if data.get("transcript_path") and Path(data["transcript_path"]).exists():
        log_commands(data["transcript_path"])
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
