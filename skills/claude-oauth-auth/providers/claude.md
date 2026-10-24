---
name: claude-oauth-auth
description: How to authenticate with Claude using a subscription OAuth token instead of an API key. Use when setting up Claude Code sessions, building tools that invoke the claude CLI, or when a user has a Claude subscription but no API key.
user-invocable: false
---

# Claude OAuth Authentication (no API key needed)

**Requirement:** the user must have an active Claude subscription (Pro, Max, or Team) for this method to work. With a subscription, the `claude` CLI supports authentication via `CLAUDE_CODE_OAUTH_TOKEN` instead of `ANTHROPIC_API_KEY` — no API key is required.

## Usage

Set the environment variable and invoke `claude` normally — no API key required:

```bash
CLAUDE_CODE_OAUTH_TOKEN=<token> claude -p "your prompt"
```

In Docker/containers, pass it as an `-e` flag:

```bash
docker run -e CLAUDE_CODE_OAUTH_TOKEN=<token> <image> claude -p "your prompt"
```

In a tmux session, inject via `tmux set-environment` then load with:

```bash
eval "$(tmux show-environment -s)" && claude
```

## Priority

If both `CLAUDE_CODE_OAUTH_TOKEN` and `ANTHROPIC_API_KEY` are present, Claude Code prefers the OAuth token.

## Notes

- The CLI handles token validation and refresh internally — do not manage the OAuth flow yourself.
- Store the token as a file at `~/.config/<yourapp>/.secrets/CLAUDE_CODE_OAUTH_TOKEN` and load it at runtime to avoid hardcoding.
- Never log or expose the token value.

## Getting and renewing the token

- The operator generates the token personally: run `claude setup-token` (requires a Claude subscription) in an interactive terminal on a machine where you can complete the browser sign-in. Never run it through an agent tool call, a CI job or a logged or recorded shell: it prints the token. Copy it straight into the token file described in Notes, never into a chat; make that file readable only by its owner (for example mode `0600`) and keep it outside any repository. For a headless host, copy it into that host's secret store instead of signing in there.
- A `claude setup-token` token is long-lived but expires, and `/login` does not renew it. The stored `/login` sign-in typically expires at the same time with the same `401`, so one `401` does not tell you which credential failed. To renew: (1) remove the old token from the shell and from any persistent user or service environment, because a token still set there overrides fresh `/login` credentials; (2) for interactive use, run `claude`, then `/logout` and `/login` with the subscription account, and confirm with `/status`; (3) the operator runs `claude setup-token` again as above, stores the new value, and checks from a new shell. A working editor-extension session is not evidence that the CLI is authenticated: it keeps its own credentials.

## Scope and safe checks

- The token is for the `claude` CLI and tools that run it. Do not use it for direct Anthropic API requests (for example `/v1/messages` from an HTTP client or the Anthropic client SDK): a subscription is throttled there. Use `ANTHROPIC_API_KEY` for direct API work.
- Do not combine the token with `claude -p --bare`: bare mode skips OAuth and keychain reads and expects `ANTHROPIC_API_KEY` or an `apiKeyHelper`, so subscription credentials, including this token, are not expected to work there. Anthropic has said `--bare` will become the default for `-p` in a future release; that is a forecast, so if `claude -p` starts failing authentication after an upgrade, check for bare mode first.
- To keep usage on the subscription, do not rely on the priority rule alone: make sure no API key reaches `claude` in that environment. Unset `ANTHROPIC_API_KEY`, and do not configure an `apiKeyHelper` or any other API key in Claude Code settings there.
- Check authentication by its effect, not by displaying the token: run `claude -p "reply ok" --model haiku` and check the exit code. Exit 0 shows only that some credential works. It proves the token only when the variable is confirmed set (test that it is non-empty without printing it) and no other credential is configured, for example in a clean container. Otherwise check each path separately: once with the variable set and once with it cleared.
- Loading the token from its file into the environment of the `claude` process is the intended use. Never send the value to stdout, a log or a transcript: do not `echo`, `cat`, `grep` or otherwise print the variable or its file, and check the file with metadata only (exists, size, permissions).
