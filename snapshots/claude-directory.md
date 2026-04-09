Claude Code reads instructions, settings, skills, subagents, and memory from your project directory and from `~/.claude` in your home directory. Commit project files to git to share them with your team; files in `~/.claude` are personal configuration that applies across all your projects. If you set [`CLAUDE_CONFIG_DIR`](</docs/en/env-vars>), every `~/.claude` path on this page lives under that directory instead. Most users only edit `CLAUDE.md` and `settings.json`. The rest of the directory is optional: add skills, rules, or subagents as you need them. This page is an interactive explorer: click files in the tree to see what each one does, when it loads, and an example. For a quick reference, see the file reference table below.

##

​

What’s not shown

The explorer covers files you author and edit. A few related files live elsewhere:

File| Location| Purpose
---|---|---
`managed-settings.json`| System-level, varies by OS| Enterprise-enforced settings that you can’t override. See [server-managed settings](</docs/en/server-managed-settings>).
`CLAUDE.local.md`| Project root| Your private preferences for this project, loaded alongside CLAUDE.md. Create it manually and add it to `.gitignore`.
Installed plugins| `~/.claude/plugins/`| Cloned marketplaces, installed plugin versions, and per-plugin data, managed by `claude plugin` commands. Orphaned versions are deleted 7 days after a plugin update or uninstall. See [plugin caching](</docs/en/plugins-reference#plugin-caching-and-file-resolution>).

`~/.claude` also holds data Claude Code writes as you work: transcripts, prompt history, file snapshots, caches, and logs. See application data below.

##

​

File reference

This table lists every file the explorer covers. Project-scope files live in your repo under `.claude/` (or at the root for `CLAUDE.md`, `.mcp.json`, and `.worktreeinclude`). Global-scope files live in `~/.claude/` and apply across all projects.

Several things can override what you put in these files:

  * [Managed settings](</docs/en/server-managed-settings>) deployed by your organization take precedence over everything
  * CLI flags like `--permission-mode` or `--settings` override `settings.json` for that session
  * Some environment variables take precedence over their equivalent setting, but this varies: check the [environment variables reference](</docs/en/env-vars>) for each one

See [settings precedence](</docs/en/settings#settings-precedence>) for the full order.

Click a filename to open that node in the explorer above.

File| Scope| Commit| What it does| Reference
---|---|---|---|---
`CLAUDE.md`| Project and global| ✓| Instructions loaded every session| [Memory](</docs/en/memory>)
`rules/*.md`| Project and global| ✓| Topic-scoped instructions, optionally path-gated| [Rules](</docs/en/memory#organize-rules-with-claude/rules/>)
`settings.json`| Project and global| ✓| Permissions, hooks, env vars, model defaults| [Settings](</docs/en/settings>)
`settings.local.json`| Project only| | Your personal overrides, auto-gitignored| [Settings scopes](</docs/en/settings#settings-files>)
`.mcp.json`| Project only| ✓| Team-shared MCP servers| [MCP scopes](</docs/en/mcp#mcp-installation-scopes>)
`.worktreeinclude`| Project only| ✓| Gitignored files to copy into new worktrees| [Worktrees](</docs/en/common-workflows#copy-gitignored-files-to-worktrees>)
`skills/<name>/SKILL.md`| Project and global| ✓| Reusable prompts invoked with `/name` or auto-invoked| [Skills](</docs/en/skills>)
`commands/*.md`| Project and global| ✓| Single-file prompts; same mechanism as skills| [Skills](</docs/en/skills>)
`output-styles/*.md`| Project and global| ✓| Custom system-prompt sections| [Output styles](</docs/en/output-styles>)
`agents/*.md`| Project and global| ✓| Subagent definitions with their own prompt and tools| [Subagents](</docs/en/sub-agents>)
`agent-memory/<name>/`| Project and global| ✓| Persistent memory for subagents| [Persistent memory](</docs/en/sub-agents#enable-persistent-memory>)
`~/.claude.json`| Global only| | App state, OAuth, UI toggles, personal MCP servers| [Global config](</docs/en/settings#global-config-settings>)
`projects/<project>/memory/`| Global only| | Auto memory: Claude’s notes to itself across sessions| [Auto memory](</docs/en/memory#auto-memory>)
`keybindings.json`| Global only| | Custom keyboard shortcuts| [Keybindings](</docs/en/keybindings>)

##

​

Check what loaded

The explorer shows what files can exist. To see what actually loaded in your current session, use these commands:

Command| Shows
---|---
`/context`| Token usage by category: system prompt, memory files, skills, MCP tools, and messages
`/memory`| Which CLAUDE.md and rules files loaded, plus auto-memory entries
`/agents`| Configured subagents and their settings
`/hooks`| Active hook configurations
`/mcp`| Connected MCP servers and their status
`/skills`| Available skills from project, user, and plugin sources
`/permissions`| Current allow and deny rules
`/doctor`| Installation and configuration diagnostics

Run `/context` first for the overview, then the specific command for the area you want to investigate.

##

​

Application data

Beyond the config you author, `~/.claude` holds data Claude Code writes during sessions. These files are plaintext. Anything that passes through a tool lands in a transcript on disk: file contents, command output, pasted text.

###

​

Cleaned up automatically

Files in the paths below are deleted on startup once they’re older than [`cleanupPeriodDays`](</docs/en/settings#available-settings>). The default is 30 days.

Path under `~/.claude/`| Contents
---|---
`projects/<project>/<session>.jsonl`| Full conversation transcript: every message, tool call, and tool result
`projects/<project>/<session>/tool-results/`| Large tool outputs spilled to separate files
`file-history/<session>/`| Pre-edit snapshots of files Claude changed, used for [checkpoint restore](</docs/en/checkpointing>)
`plans/`| Plan files written during [plan mode](</docs/en/permission-modes#analyze-before-you-edit-with-plan-mode>)
`debug/`| Per-session debug logs, written only when you start with `--debug` or run `/debug`
`paste-cache/`, `image-cache/`| Contents of large pastes and attached images
`session-env/`| Per-session environment metadata

###

​

Kept until you delete them

The following paths are not covered by automatic cleanup and persist indefinitely.

Path under `~/.claude/`| Contents
---|---
`history.jsonl`| Every prompt you’ve typed, with timestamp and project path. Used for up-arrow recall.
`stats-cache.json`| Aggregated token and cost counts shown by `/cost`
`backups/`| Timestamped copies of `~/.claude.json` taken before config migrations
`todos/`| Legacy per-session task lists. No longer written by current versions; safe to delete.

`shell-snapshots/` holds runtime files removed when the session exits cleanly. Other small cache and lock files appear depending on which features you use and are safe to delete.

###

​

Plaintext storage

Transcripts and history are not encrypted at rest. OS file permissions are the only protection. If a tool reads a `.env` file or a command prints a credential, that value is written to `projects/<project>/<session>.jsonl`. To reduce exposure:

  * Lower `cleanupPeriodDays` to shorten how long transcripts are kept
  * In non-interactive mode, pass `--no-session-persistence` alongside `-p` to skip writing transcripts entirely. In the Agent SDK, set `persistSession: false`. There is no interactive-mode equivalent.
  * Use [permission rules](</docs/en/permissions>) to deny reads of credential files

###

​

Clear local data

You can delete any of the application-data paths above at any time. New sessions are unaffected. The table below shows what you lose for past sessions.

Delete| You lose
---|---
`~/.claude/projects/`| Resume, continue, and rewind for past sessions
`~/.claude/history.jsonl`| Up-arrow prompt recall
`~/.claude/file-history/`| Checkpoint restore for past sessions
`~/.claude/stats-cache.json`| Historical totals shown by `/cost`
`~/.claude/backups/`| Rollback copies of `~/.claude.json` from past config migrations
`~/.claude/debug/`, `~/.claude/plans/`, `~/.claude/paste-cache/`, `~/.claude/image-cache/`, `~/.claude/session-env/`| Nothing user-facing
`~/.claude/todos/`| Nothing. Legacy directory not written by current versions.

Don’t delete `~/.claude.json`, `~/.claude/settings.json`, or `~/.claude/plugins/`: those hold your auth, preferences, and installed plugins.

##

​

Related resources

  * [Manage Claude’s memory](</docs/en/memory>): write and organize CLAUDE.md, rules, and auto memory
  * [Configure settings](</docs/en/settings>): set permissions, hooks, environment variables, and model defaults
  * [Create skills](</docs/en/skills>): build reusable prompts and workflows
  * [Configure subagents](</docs/en/sub-agents>): define specialized agents with their own context
