Claude Code integrates with JetBrains IDEs through a dedicated plugin, providing features like interactive diff viewing, selection context sharing, and more.

##

​

Supported IDEs

The Claude Code plugin works with most JetBrains IDEs, including:

  * IntelliJ IDEA
  * PyCharm
  * Android Studio
  * WebStorm
  * PhpStorm
  * GoLand

##

​

Features

  * **Quick launch** : use `Cmd+Esc` (Mac) or `Ctrl+Esc` (Windows/Linux) to open Claude Code directly from your editor, or click the Claude Code button in the UI
  * **Diff viewing** : code changes can be displayed directly in the IDE diff viewer instead of the terminal
  * **Selection context** : the current selection or tab in the IDE is automatically shared with Claude Code. [`Read` deny rules](</docs/en/permissions#read-and-edit>) block this sharing for matching files
  * **File reference shortcuts** : use `Cmd+Option+K` (Mac) or `Alt+Ctrl+K` (Linux/Windows) to insert file references such as `@src/auth.ts#L1-99`
  * **Diagnostic sharing** : diagnostic errors from the IDE, such as lint and syntax errors, are automatically shared with Claude as you work

##

​

Installation

The plugin runs the `claude` command in your IDE’s integrated terminal and connects to it. It does not bundle its own copy of the CLI, so install both pieces:

1

Install the Claude Code CLI

Follow the [quickstart](</docs/en/quickstart>) to install the CLI if you haven’t already. The plugin shows a “Cannot launch Claude Code” notification when `claude` isn’t on your PATH.

2

Install the JetBrains plugin

Install the [Claude Code plugin](<https://plugins.jetbrains.com/plugin/27310-claude-code-beta->) from the JetBrains Marketplace and restart your IDE.

If `claude` is installed somewhere your IDE can’t find, set the full path in the plugin’s Claude command setting. Claude Code works with any paid Claude subscription (Pro, Max, Team, or Enterprise) or a Claude Console account, and no API key is required. You’ll be prompted to [log in](</docs/en/authentication#log-in-to-claude-code>) the first time you run `claude`.

After installing the plugin, you may need to restart your IDE completely for it to take effect.

##

​

Usage

###

​

From your IDE

Run `claude` from your IDE’s integrated terminal, and all integration features will be active.

###

​

From external terminals

Use the `/ide` command in any external terminal to connect Claude Code to your JetBrains IDE and activate all features:

    claude

    /ide

If you want Claude to have access to the same files as your IDE, start Claude Code from the same directory as your IDE project root.

##

​

Configuration

###

​

Claude Code settings

Configure IDE integration through Claude Code’s settings:

  1. Run `claude`
  2. Enter the `/config` command
  3. Set the diff tool to `auto` to show diffs in the IDE, or `terminal` to keep them in the terminal

###

​

Plugin settings

Configure the Claude Code plugin by going to **Settings → Tools → Claude Code [Beta]** :

####

​

General settings

  * **Claude command** : specify a custom command to run Claude, for example `claude`, `/usr/local/bin/claude`, or `npx @anthropic-ai/claude-code`
  * **Suppress notification for Claude command not found** : skip notifications about not finding the Claude command
  * **Enable using Option+Enter for multi-line prompts** : on macOS only. When enabled, Option+Enter inserts new lines in Claude Code prompts. Disable if the Option key is being captured unexpectedly. Requires a terminal restart.
  * **Enable automatic updates** : automatically check for and install plugin updates, applied on restart

For WSL users: Set `wsl -d Ubuntu -- bash -lic "claude"` as your Claude command (replace `Ubuntu` with your WSL distribution name)

####

​

ESC key configuration

If the ESC key doesn’t interrupt Claude Code operations in JetBrains terminals:

  1. Go to **Settings → Tools → Terminal**
  2. Either:
     * Uncheck “Move focus to the editor with Escape”, or
     * Click “Configure terminal keybindings” and delete the “Switch focus to Editor” shortcut
  3. Apply the changes

This allows the ESC key to properly interrupt Claude Code operations.

##

​

Special configurations

###

​

Remote development

When using JetBrains Remote Development, you must install the plugin in the remote host via **Settings → Plugin (Host)**.

The plugin must be installed on the remote host, not on your local client machine.

###

​

WSL configuration

If you’re using Claude Code on WSL2 with a JetBrains IDE and see “No available IDEs detected”, the cause is usually WSL2’s NAT networking or Windows Firewall blocking the connection between WSL2 and the IDE running on the Windows host. WSL1 uses the host’s network directly and isn’t affected.

####

​

Allow WSL2 traffic through Windows Firewall

This is the recommended fix because it keeps your existing WSL2 networking mode.

1

Find your WSL2 IP address

From inside your WSL shell, run:

    hostname -I

Note the subnet, for example `172.21.123.45` is in `172.21.0.0/16`.

2

Create a firewall rule

Open PowerShell as Administrator and run the following, adjusting the IP range to match your subnet:

    New-NetFirewallRule -DisplayName "Allow WSL2 Internal Traffic" -Direction Inbound -Protocol TCP -Action Allow -RemoteAddress 172.21.0.0/16 -LocalAddress 172.21.0.0/16

3

Restart your IDE and Claude Code

Close and reopen both so the new rule takes effect.

####

​

Switch WSL2 to mirrored networking

Mirrored networking requires Windows 11 22H2 or later. If you’re on Windows 10, use the firewall rule above instead. Add this to `.wslconfig` in your Windows user directory:

    [wsl2]
    networkingMode=mirrored

Then restart WSL with `wsl --shutdown` from PowerShell.

##

​

Troubleshooting

###

​

Plugin not working

If the plugin is installed but Claude Code features don’t appear in your IDE:

  * Ensure you’re running Claude Code from the project root directory
  * Check that the JetBrains plugin is enabled in the IDE settings
  * Completely restart the IDE (you may need to do this multiple times)
  * For Remote Development, ensure the plugin is installed in the remote host

###

​

IDE not detected

If running `claude` shows “No available IDEs detected”:

  * Verify the plugin is installed and enabled
  * Restart the IDE completely
  * Check that you’re running Claude Code from the integrated terminal
  * For WSL users, see WSL configuration above

###

​

Command not found

If clicking the Claude icon shows “command not found”:

  1. Verify Claude Code is installed by running `claude --version` in a terminal
  2. Configure the Claude command path in plugin settings
  3. For WSL users, use the WSL command format mentioned in the configuration section

##

​

Security considerations

When Claude Code runs in a JetBrains IDE in [`acceptEdits` permission mode](</docs/en/permission-modes#auto-approve-file-edits-with-acceptedits-mode>), it may be able to modify IDE configuration files that can be automatically executed by your IDE. This may increase the risk of running Claude Code in `acceptEdits` mode and allow bypassing Claude Code’s permission prompts for bash execution. When running in JetBrains IDEs, consider:

  * Using manual approval mode for edits
  * Taking extra care to ensure Claude is only used with trusted prompts
  * Being aware of which files Claude Code has access to modify

For Claude Code installation or login problems outside the IDE, see [Troubleshoot installation and login](</docs/en/troubleshoot-install>).

###

​

The built-in IDE MCP server

When the plugin is active, it runs a local MCP server that the CLI connects to automatically. This is how the CLI opens diffs in the IDE’s native diff viewer, reads your current selection for `@`-mentions, and pulls inspection diagnostics into the conversation. The server is named `ide` and is hidden from `/mcp` because there’s nothing to configure. If your organization uses a [`PreToolUse` hook](</docs/en/hooks#pretooluse>) to allowlist MCP tools, though, you’ll need to know it exists. **Selection and open-file context.** While connected, the CLI includes your current editor selection and the path of the active file as context on each prompt you send. The transcript shows a `⧉ Selected N lines from <file>` line when this happens. To exclude a sensitive file such as `.env`, add a [`Read` deny rule](</docs/en/permissions#read-and-edit>) for its path. A matching deny rule prevents both the selected text and the open-file notice for that file from reaching Claude. **Transport and authentication.** The server listens on an OS-assigned ephemeral port, and the port is not configurable. The transport is unencrypted `ws://`; on loopback, any process that could capture the traffic can also read the token from the lock file, so TLS would not add protection against a local attacker. Each IDE start generates a fresh random auth token, writes it to a lock file at `~/.claude/ide/<port>.lock`, and the CLI must present it as the `X-Claude-Code-Ide-Authorization` header to connect. If `CLAUDE_CONFIG_DIR` is set, the lock file is written to `$CLAUDE_CONFIG_DIR/ide/` instead. **Tools exposed to the model.** The server hosts several tools, but only one is visible to the model. The rest are internal RPC the CLI uses for its own UI, such as opening diffs and reading selections, and are filtered out before the tool list reaches Claude.

Tool name (as seen by hooks)| What it does| Read-only
---|---|---
`mcp__ide__getDiagnostics`| Returns the IDE’s inspection diagnostics, the errors and warnings shown in the editor. Optionally scoped to one file.| Yes

The JetBrains plugin does not expose a code-execution tool to the model. **Listening interface.** Which network interface the server binds to is controlled by **Accept connections from all network interfaces** under **Settings → Tools → Claude Code [Beta] → Networking (Advanced)**. With the setting disabled, the server listens on `127.0.0.1` only and is not reachable from other hosts. With it enabled, the port is reachable from your local network. The setting exists for cases where the CLI cannot reach the IDE over loopback, such as WSL2 with default NAT networking or a remote-IDE setup; see WSL configuration for that scenario.

Enabling **Accept connections from all network interfaces** makes the IDE MCP port reachable from your local network. Connections still require the auth token from the lock file, but because the transport is unencrypted `ws://`, both the session traffic and that token cross the network in cleartext when the setting is on. Only turn it on when loopback genuinely cannot work. For WSL2, prefer mirrored networking so the Windows loopback interface is shared with the Linux VM and the socket can stay on loopback.
