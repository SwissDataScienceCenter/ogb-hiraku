---
name: hiraku
description: Manage data science and research projects using Hiraku. Use when users ask to create, inspect, or update research records; launch or monitor jobs; inspect runs; execute workflows; or review literature. For experiment records that test or compare approaches, delegate design before writing the record. For implementation or requests to run end to end, delegate implementation and results analysis to the configured project subagents.
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
relationships separate from its metadata fields.

## Specialist delegation

Check the project's configured agents and delegate each matching phase to its
specialist. When the matching subagent is available, delegation is required;
do not silently perform that phase yourself. Invoke the configured subagent by
its exact name through the host's subagent feature, then wait for its result;
reading its definition or mentioning the role does not count as delegation.

- **Literature review:** For paper discovery, cited evidence, or research gaps,
  delegate to `literature-reviewer`. It follows the
  `hiraku-literature-review` skill and saves a cited synthesis in a context
  record.
- **Hypothesis and design:** For requests to test an idea or compare approaches,
  delegate to `hypothesis-designer` before creating or updating the experiment
  record. It follows the `hiraku-hypothesis-design` skill's generate → critique
  → compare → refine → select procedure. This includes phrasing such as “create
  a new record testing X rather than Y.” Wait for its selected falsifiable
  hypothesis and experiment proposal, then create or update the record yourself
  from that proposal.
- **Implementation and execution:** When the user asks to implement, run, or
  take an existing experiment end to end, delegate to `experiment-implementer`.
  Pass the active record ID, agreed design, and the user's request. A direct
  request to run or take it end to end authorizes the run; do not bypass the
  subagent by submitting the job yourself. If the job is still running, report
  that state accurately.
- **Results analysis:** When asked to analyze results, or after a requested
  end-to-end experiment has produced tracked results, delegate to
  `results-analyst`. Pass the hypothesis, design, baseline, and run/job IDs.
  Wait for its analysis before summarizing conclusions to the user.

Follow-up requests such as “run it” or “take it end to end” refer to the active
experiment unless the user says otherwise. Run dependent phases in order: wait
for the design before recording it, and wait for tracked results before asking
the analyst to interpret them. Do not start phases the user did not request.
Give each specialist the goal, relevant record IDs, available evidence, and a
clear expected output. Keep the main agent responsible for user communication,
integrating results, and deciding what to save. If the required subagent is not
available, do the work directly and state that delegation was unavailable.
Subagent role instructions guide behavior; rely on host-enforced permissions
for actual tool restrictions.

## Jobs and tracked evidence

For agent-launched commands, prefer submitting through the connected `job_submit`
MCP tool. Submit the command as an argv list and include explicit record
attribution. Submission defaults to background execution with `local-detached`
and returns an ID; read command output with `job_logs` and check execution
state with `job_status` or `job_list`. Stop a running job with `job_cancel`;
from the CLI, use `hiraku job cancel JOB_ID`.

Omitting `record_id` submits an unattributed job.
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
hiraku record list --json
hiraku record create tasks/question --title "Research question" --type task
hiraku job submit --record tasks/question -- uv run python train.py --seed 42
hiraku job status JOB_ID
hiraku leaderboard runs --record tasks/question --json
```

Use `hiraku <command> --help` for current options. See the
[Hiraku documentation](https://swissdatasciencecenter.github.io/hiraku/) for
project setup, records, tracking, jobs, and workflows.
