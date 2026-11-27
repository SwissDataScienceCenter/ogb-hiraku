---
id: collaborative
description: Draft, implement, launch, and analyze experiments with the user, step by step.
rules: >-
  Use Hiraku's record and run tools, or the `hiraku` CLI (`hiraku record show`,
  `hiraku record list`, `hiraku leaderboard runs`), to read the task and earlier
  experiments. Never delete records or rewrite Git history.
---
# Collaborative research

## Draft

Draft one experiment for the task. Read the task record and its earlier
experiments first, and build on the previous results in the data. Do not
change code yet. Present the draft to the user, then call the MCP tool
`workflow_approval` with the workflow session ID, current interrupt ID, concise summary,
and the proposed response. Wait for the user's choice, then pass the returned
result to `workflow_resume`. For an approved draft, the proposed
response is `{"event": "drafted", "arguments":
{"name": "...", "summary": "...", "hypothesis": "...", "change":
"..."}}`.
For any revision request, the user may leave feedback blank. If the elicitation
is cancelled, explain that approval was not given and leave the workflow paused;
do not resume it or proceed with the experiment.

## Implement

Implement the drafted experiment in the data and commit the change. Show
the user the change, then call `workflow_approval` with the proposed response.
Pass the returned result to `workflow_resume`.

## Launch

Call `workflow_approval` with the interrupt ID and `{"event": "launched"}` as
the proposed response. Run the explicit argv supplied when starting the
workflow with `hiraku run --record <experiment> -- <command...>` only after
approval, then resume with the result once the run is tracked; check with
`hiraku leaderboard runs --record <experiment>`.

## Analyze

Compare the runs in the selected leaderboard with the task's objectives, earlier results, and
the experiment's hypothesis. Present your verdict and conclusion to the user,
then call `workflow_approval` with the proposed analysis response and wait.
Pass the returned result to `workflow_resume`.

## Done

Summarize the run for the user: each experiment in the data's
`results` with its verdict, and what you would try next.
