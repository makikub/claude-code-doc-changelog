Slash commands provide a way to control Claude Code sessions with special commands that start with `/`. These commands can be sent through the SDK to perform actions like clearing conversation history, compacting messages, or getting help.

##

​

Discovering Available Slash Commands

The Claude Agent SDK provides information about available slash commands in the system initialization message. Access this information when your session starts:

TypeScript

Python

    import { query } from "@anthropic-ai/claude-agent-sdk";

    for await (const message of query({
      prompt: "Hello Claude",
      options: { maxTurns: 1 }
    })) {
      if (message.type === "system" && message.subtype === "init") {
        console.log("Available slash commands:", message.slash_commands);
        // Example output: ["/compact", "/clear", "/help"]
      }
    }

##

​

Sending Slash Commands

Send slash commands by including them in your prompt string, just like regular text:

TypeScript

Python

    import { query } from "@anthropic-ai/claude-agent-sdk";

    // Send a slash command
    for await (const message of query({
      prompt: "/compact",
      options: { maxTurns: 1 }
    })) {
      if (message.type === "result") {
        console.log("Command executed:", message.result);
      }
    }

##

​

Common Slash Commands

###

​

`/compact` \- Compact Conversation History

The `/compact` command reduces the size of your conversation history by summarizing older messages while preserving important context:

TypeScript

Python

    import { query } from "@anthropic-ai/claude-agent-sdk";

    for await (const message of query({
      prompt: "/compact",
      options: { maxTurns: 1 }
    })) {
      if (message.type === "system" && message.subtype === "compact_boundary") {
        console.log("Compaction completed");
        console.log("Pre-compaction tokens:", message.compact_metadata.pre_tokens);
        console.log("Trigger:", message.compact_metadata.trigger);
      }
    }

###

​

`/clear` \- Clear Conversation

The `/clear` command starts a fresh conversation by clearing all previous history:

TypeScript

Python

    import { query } from "@anthropic-ai/claude-agent-sdk";

    // Clear conversation and start fresh
    for await (const message of query({
      prompt: "/clear",
      options: { maxTurns: 1 }
    })) {
      if (message.type === "system" && message.subtype === "init") {
        console.log("Conversation cleared, new session started");
        console.log("Session ID:", message.session_id);
      }
    }

##

​

Creating Custom Slash Commands

In addition to using built-in slash commands, you can create your own custom commands that are available through the SDK. Custom commands are defined as markdown files in specific directories, similar to how subagents are configured.

The `.claude/commands/` directory is the legacy format. The recommended format is `.claude/skills/<name>/SKILL.md`, which supports the same slash-command invocation (`/name`) plus autonomous invocation by Claude. See [Skills](</docs/en/agent-sdk/skills>) for the current format. The CLI continues to support both formats, and the examples below remain accurate for `.claude/commands/`.

###

​

File Locations

Custom slash commands are stored in designated directories based on their scope:

  * **Project commands** : `.claude/commands/` \- Available only in the current project (legacy; prefer `.claude/skills/`)
  * **Personal commands** : `~/.claude/commands/` \- Available across all your projects (legacy; prefer `~/.claude/skills/`)

###

​

File Format

Each custom command is a markdown file where:

  * The filename (without `.md` extension) becomes the command name
  * The file content defines what the command does
  * Optional YAML frontmatter provides configuration

####

​

Basic Example

Create `.claude/commands/refactor.md`:

    Refactor the selected code to improve readability and maintainability.
    Focus on clean code principles and best practices.

This creates the `/refactor` command that you can use through the SDK.

####

​

With Frontmatter

Create `.claude/commands/security-check.md`:

    ---
    allowed-tools: Read, Grep, Glob
    description: Run security vulnerability scan
    model: claude-opus-4-6
    ---

    Analyze the codebase for security vulnerabilities including:
    - SQL injection risks
    - XSS vulnerabilities
    - Exposed credentials
    - Insecure configurations

###

​

Using Custom Commands in the SDK

Once defined in the filesystem, custom commands are automatically available through the SDK:

TypeScript

Python

    import { query } from "@anthropic-ai/claude-agent-sdk";

    // Use a custom command
    for await (const message of query({
      prompt: "/refactor src/auth/login.ts",
      options: { maxTurns: 3 }
    })) {
      if (message.type === "assistant") {
        console.log("Refactoring suggestions:", message.message);
      }
    }

    // Custom commands appear in the slash_commands list
    for await (const message of query({
      prompt: "Hello",
      options: { maxTurns: 1 }
    })) {
      if (message.type === "system" && message.subtype === "init") {
        // Will include both built-in and custom commands
        console.log("Available commands:", message.slash_commands);
        // Example: ["/compact", "/clear", "/help", "/refactor", "/security-check"]
      }
    }

###

​

Advanced Features

####

​

Arguments and Placeholders

Custom commands support dynamic arguments using placeholders: Create `.claude/commands/fix-issue.md`:

    ---
    argument-hint: [issue-number] [priority]
    description: Fix a GitHub issue
    ---

    Fix issue #$1 with priority $2.
    Check the issue description and implement the necessary changes.

Use in SDK:

TypeScript

Python

    import { query } from "@anthropic-ai/claude-agent-sdk";

    // Pass arguments to custom command
    for await (const message of query({
      prompt: "/fix-issue 123 high",
      options: { maxTurns: 5 }
    })) {
      // Command will process with $1="123" and $2="high"
      if (message.type === "result") {
        console.log("Issue fixed:", message.result);
      }
    }

####

​

Bash Command Execution

Custom commands can execute bash commands and include their output: Create `.claude/commands/git-commit.md`:

    ---
    allowed-tools: Bash(git add:*), Bash(git status:*), Bash(git commit:*)
    description: Create a git commit
    ---

    ## Context

    - Current status: !`git status`
    - Current diff: !`git diff HEAD`

    ## Task

    Create a git commit with appropriate message based on the changes.

####

​

File References

Include file contents using the `@` prefix: Create `.claude/commands/review-config.md`:

    ---
    description: Review configuration files
    ---

    Review the following configuration files for issues:
    - Package config: @package.json
    - TypeScript config: @tsconfig.json
    - Environment config: @.env

    Check for security issues, outdated dependencies, and misconfigurations.

###

​

Organization with Namespacing

Organize commands in subdirectories for better structure:

    .claude/commands/
    ├── frontend/
    │   ├── component.md      # Creates /component (project:frontend)
    │   └── style-check.md     # Creates /style-check (project:frontend)
    ├── backend/
    │   ├── api-test.md        # Creates /api-test (project:backend)
    │   └── db-migrate.md      # Creates /db-migrate (project:backend)
    └── review.md              # Creates /review (project)

The subdirectory appears in the command description but doesn’t affect the command name itself.

###

​

Practical Examples

####

​

Code Review Command

Create `.claude/commands/code-review.md`:

    ---
    allowed-tools: Read, Grep, Glob, Bash(git diff:*)
    description: Comprehensive code review
    ---

    ## Changed Files
    !`git diff --name-only HEAD~1`

    ## Detailed Changes
    !`git diff HEAD~1`

    ## Review Checklist

    Review the above changes for:
    1. Code quality and readability
    2. Security vulnerabilities
    3. Performance implications
    4. Test coverage
    5. Documentation completeness

    Provide specific, actionable feedback organized by priority.

####

​

Test Runner Command

Create `.claude/commands/test.md`:

    ---
    allowed-tools: Bash, Read, Edit
    argument-hint: [test-pattern]
    description: Run tests with optional pattern
    ---

    Run tests matching pattern: $ARGUMENTS

    1. Detect the test framework (Jest, pytest, etc.)
    2. Run tests with the provided pattern
    3. If tests fail, analyze and fix them
    4. Re-run to verify fixes

Use these commands through the SDK:

TypeScript

Python

    import { query } from "@anthropic-ai/claude-agent-sdk";

    // Run code review
    for await (const message of query({
      prompt: "/code-review",
      options: { maxTurns: 3 }
    })) {
      // Process review feedback
    }

    // Run specific tests
    for await (const message of query({
      prompt: "/test auth",
      options: { maxTurns: 5 }
    })) {
      // Handle test results
    }

##

​

See Also

  * [Slash Commands](</docs/en/skills>) \- Complete slash command documentation
  * [Subagents in the SDK](</docs/en/agent-sdk/subagents>) \- Similar filesystem-based configuration for subagents
  * [TypeScript SDK reference](</docs/en/agent-sdk/typescript>) \- Complete API documentation
  * [SDK overview](</docs/en/agent-sdk/overview>) \- General SDK concepts
  * [CLI reference](</docs/en/cli-reference>) \- Command-line interface
