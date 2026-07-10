# Agents

SynapSideKick uses Claude Code's project-subagent system for delegated work, rather than a
separate orchestration layer. There's one entry point: the master agent, which is just the
default Claude Code session running in this repo — that's who you talk to. It delegates
focused tasks to specialized subagents; those subagents are never invoked directly by you,
only by the master agent (via the Agent tool).

The subagent *definitions* have to live in `.claude/agents/*.md` for Claude Code to
auto-discover them (a top-level `agents/` folder is not scanned) — this folder is the
human-readable index of what exists and why.

Source: [Claude Code subagent docs](https://code.claude.com/docs/en/subagents-and-plugins.md)
— required frontmatter is `name` + `description`; `tools` is a comma-separated list; the
markdown body becomes the subagent's system prompt.

## Current subagents

| Subagent | Definition | Scope |
|---|---|---|
| `maxwell-hardware` | [.claude/agents/maxwell-hardware.md](../.claude/agents/maxwell-hardware.md) | Starting/stopping the Maxwell rig (`mxwserver`), checking online status, driving the MaxLab Python API (chip init, well activation). Wraps `synapconnect/hardware/maxwell/`. |

Add new subagents here as they're created, one row per subagent, pointing at its `.claude/agents/` definition.
