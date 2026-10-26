# Document output contract

The single owner of WHERE a skill saves an operator-facing document and HOW it reports
the location. A document here is a durable deliverable the operator reads later: an HTML
proposal, a guided tour, a report, a digest. Chat output, task-state files, plans, and code
are not documents under this contract and keep their own homes.

Adopted in Skill Mesh v2.0.1. Before v2.0.1 the Claude profile published these documents
as private hosted Artifacts (a `https://claude.ai/artifact/...` URL) and the Codex and
Copilot profiles wrote them beside the plan under `documentation/`. Both forms are retired:
every provider now writes the same file to the same place.

## Rules

1. **Location.** Save the document inside the target project repository at
   `docs/<skill-name>/<document-slug>.html` (or `.md` when the core says the document is
   Markdown), where `<skill-name>` is the producing skill's catalog name exactly
   (`plan-redline`, `repo-update`, ...). Create the directory when it is missing. The
   project root is the repository the skill is acting on, resolved the way the core resolves
   it (`PROJECT_ROOT`, the plan's repository, or the cwd repository, in the core's order).
2. **Slug.** `<document-slug>` is stable across republications of the same document so a
   republish overwrites the same file. Slugify every component the same way: lower-case,
   every run of characters outside `[a-z0-9]` replaced by one hyphen, no leading or trailing
   hyphen, no dates. `<project-slug>` is the repository name (the repo part of the GitHub
   `owner/repo` slug when known, else the Git toplevel directory name) slugified; `<plan-slug>`
   is `<project-slug>` for the project's canonical plan (`plan.md`, `master_plan.md`) and
   `<project-slug>-<plan-file-stem>` for any other plan file. The proposal's document slug is
   `<plan-slug>-proposal`; the tour's is `<project-slug>-<phase-or-version>` where the phase
   label is slugified too (`Phase 4 — Audio Ingestion` → `phase-4`, `v0` → `v0`).
3. **Self-contained file.** One standalone HTML file: inline CSS and scripts, no CDN or
   external font dependency required to read it, token-driven light/dark theme
   (`prefers-color-scheme: dark` plus `:root[data-theme=...]` overrides), accessible
   semantic structure, real content, no placeholders. The file must render from disk
   with no server.
4. **Locator.** The stable locator the skill records and reports is the repository-relative
   POSIX path (`docs/plan-redline/<plan-slug>-proposal.html`), never an absolute path, a
   `file://` URL, or a hosted URL. Where a core records the locator in a plan or report
   line (`Proposal:`, `Tour:`), that line carries this path.
5. **No hosted copy.** Never publish, update, or mint a hosted Artifact or any other hosted
   copy of the document, on any provider, even when the host offers an Artifact tool and
   even when a prior hosted locator is recorded. A recorded hosted locator from before
   v2.0.1 is stale: write the file, replace the recorded locator with the path, and report
   the change in one line, stating that the prior hosted copy remains published and is now
   stale.
6. **Commit ownership.** The document is a repository file and follows the producing core's
   own commit rules. A core that commits in the same run includes the file in its scoped
   staging or in one additional path-scoped commit the core names (never a repository-wide
   `git add -A`); a core that does not commit leaves the file on disk, reports the path, and
   names it as uncommitted.
7. **Design skill.** When the host provides a page-design skill (`artifact-design` on
   Claude Code), load it before authoring the markup; it governs craft, not location.
   When it is unavailable, author the page without it and say so in the report line.
8. **Failure handling.** When the document is a side deliverable (the repo-update tour), a
   file that cannot be written (read-only tree, missing project root) is reported as
   `skipped (<reason>)` on the core's report line and never changes the core's primary result
   or blocks the run. When the document is the core's primary output (the plan-redline
   proposal), the core's own halt rules govern: report the reason and make no locator edit.

## Consumers

| Skill | Document | Path | Report line |
|---|---|---|---|
| `plan-redline` | P/D proposal | `docs/plan-redline/<plan-slug>-proposal.html` | `Proposal:` in the plan and the chat report |
| `repo-update` | Build-completion guided tour | `docs/repo-update/<project-slug>-<phase-or-version>.html` | `Tour:` in the final report |

A new document-producing skill adds a row here and cites this file instead of restating
the rules.
