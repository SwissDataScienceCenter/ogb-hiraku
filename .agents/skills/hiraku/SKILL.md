---
name: hiraku
description: Manage data science and research projects using Hiraku. Use when users ask to create, inspect, or update research records; launch or monitor computational jobs; inspect tracked experiment runs and leaderboards; or execute Hiraku project workflows. Prefer connected Hiraku MCP tools, with CLI fallback when available.
---

# Hiraku quickstart

Hiraku organizes data-science work around **records**, **runs**, and
**leaderboards**:

- A **record** documents a research goal, supporting context, or focused
  investigation. Records can be related as parent and child.
- A **run** is an execution trace written by a configured tracker such as
  MLflow, W&B, or CSV. Hiraku attaches record and job attribution when
  available; the training code remains responsible for logging metrics.
- A **leaderboard** defines where Hiraku reads runs and which metrics to
  compare.

## MCP quickstart

Prefer connected Hiraku MCP tools for the operations they expose. Discover the
tools through the host's tool interface; the host may prefix their names. Rely
on the schemas provided by the host. The server is scoped to the project
selected by the host, so no project argument is needed. Check project settings
before changing project state.

Inspect the project and its records, then read relevant records before making
changes. Reuse an existing record when it matches the task. Record IDs are paths under
`hiraku/records/`, without `.md`. Relationships use `parent_id` and `related_to`,
independently of directory placement. Fields are local to each record; read
related records explicitly when their context matters.

Create a record when requested or needed for the task. Keep its identity and
relationships separate from its metadata fields. Creation activates the record
by default; leave supporting records inactive when they should not change the
project-wide active record. Record updates merge metadata fields, while a
supplied Markdown body replaces the whole body. Preserve existing content the
task does not change.

## Jobs and tracked evidence

For agent-launched commands, prefer submitting through the connected `job_submit`
MCP tool. Submit the command as an argv list and include explicit record
attribution. Submission defaults to background execution with `local-detached`
and returns an ID; monitor it with `job_status` or `job_list`.

Omitting `record_id` submits an unattributed job even if a record is active.
Submission is not completion. If submission reports a history-write failure,
inspect existing jobs before retrying: execution may already have started. Use
CLI `hiraku run` for foreground streaming when that is specifically needed; use
the CLI `hiraku job submit` only when the MCP tools are unavailable or the user
asks for CLI commands.

Discover configured leaderboards before reading runs, and select one explicitly
when several exist. Hiraku reads runs
from its configured tracking source; training code must log metrics and record
attribution. A submitted job does not automatically create a tracked run.
Record findings from observed results and include relevant job/run IDs and
metrics; distinguish missing evidence from a failed experiment.

## Project workflows

For a requested workflow, discover available workflows and inspect its
definition at `hiraku://workflows/{workflow_id}` when needed. Start it with the
workflow ID and input arguments. Follow the returned interrupt and response
schema.

Continue an existing session by checking its status and resuming with the
current checkpoint; do not start a new session to continue paused work. Inspect
the current checkpoint state before repeating actions.

When an interrupt requests approval, use the approval tool to present a concise
proposal and proposed response through structured MCP elicitation. Resume with
the accepted result and current checkpoint. If elicitation is cancelled or
declined, leave the session paused. Do not fabricate approval.

## CLI fallback

When MCP tools are unavailable or the user asks for CLI commands, use the CLI:

```bash
hiraku status --json
hiraku record list --json
hiraku record create tasks/question --title "Research question" --type task
hiraku job submit --record tasks/question -- uv run python train.py --seed 42
hiraku job status JOB_ID
hiraku leaderboard runs --record tasks/question --json
```

Use `hiraku <command> --help` for current options. See the
[Hiraku documentation](https://swissdatasciencecenter.github.io/hiraku/) for
project setup, records, tracking, jobs, and workflows.
