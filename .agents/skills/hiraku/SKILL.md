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
tools through the host's tool interface and use their advertised schemas;
the host may prefix the names shown below. The examples show a tool name and
its JSON arguments, not Python or shell commands. The server is scoped to the
project selected by the host, so no project argument is needed. Check
`project_info` before changing project state.

Inspect the project and its records with `project_info {}` and `record_list {}`;
read a record with `record_show {"record_id": "tasks/question"}`. Reuse an
existing record when it matches the task. Record IDs are paths under
`hiraku/records/`, without `.md`. Relationships use `parent_id` and `related_to`,
independently of directory placement. Fields are local to each record; read
related records explicitly when their context matters.

Create a record when requested or needed for the task. Pass its type and other
metadata in `fields`; creation activates the record by default:

```text
record_create
{
  "record_id": "tasks/question",
  "title": "Research question",
  "fields": {"type": "task", "goal": "...", "question": "..."},
  "markdown": "## Investigation\n\n..."
}
```

Keep identity and relationships in named arguments, outside `fields`.
Use `activate: false` when creating supporting material without switching the
project-wide active record. Read a record before updating it:
`record_update` merges `fields`, null clears a field, and `markdown` replaces
the entire body when supplied. Preserve existing content that the task does
not change.

## Jobs and tracked evidence

Submit commands as argv lists with explicit record attribution. `job_submit`
defaults to background execution with `local-detached` and returns an `id`;
check that ID with `job_status` or list jobs with `job_list`:

```text
job_submit
{
  "command": ["uv", "run", "python", "train.py", "--seed", "42"],
  "record_id": "tasks/question"
}
job_status {"job_id": "<returned-id>"}
job_list {"record_id": "tasks/question"}
```

Omitting `record_id` submits an unattributed job even if a record is active.
Submission is not completion. If submission reports a history-write failure,
inspect existing jobs before retrying: execution may already have started.
Use CLI `hiraku run` when foreground streaming and an exit code are needed.

Discover configured leaderboards with `leaderboard_list {}`. Select one
explicitly when several exist:

```text
runs {"leaderboard": "validation", "record_id": "tasks/question", "limit": 10}
```

Use a discovered leaderboard name in place of `validation`. Hiraku reads runs
from its configured tracking source; training code must log metrics and record
attribution. A submitted job does not automatically create a tracked run.
Record findings from observed results and include relevant job/run IDs and
metrics; distinguish missing evidence from a failed experiment.

## Project workflows

For a requested workflow, discover it with `workflow_list {}` and inspect its
definition at `hiraku://workflows/{workflow_id}` when needed. Start it with
`workflow_start` using its `workflow_id` and input `arguments`. Follow the
returned interrupt and response schema.

Continue an existing session with `workflow_status` and `workflow_resume`,
using its `workflow_session_id` and current `checkpoint_id`; do not start a
new session to continue paused work. Use `workflow_sessions` and
`workflow_session_history` to recover prior work before repeating actions.

When an interrupt requests approval, call `workflow_approval` with the session
ID, current `interrupt_id`, a concise `proposal`, and the proposed `response`.
It opens structured MCP elicitation. Pass its accepted result as `response`
to `workflow_resume` with the current checkpoint ID. If elicitation is
cancelled or declined, leave the session paused. Do not fabricate approval.

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
