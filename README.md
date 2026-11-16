# Hiraku Open Graph Benchmark Demo

> **Hands-on session** · Explore an existing research project, inspect its
> records and prior runs, then design and evaluate an experiment with the Hiraku
> CLI or a coding agent.

## The benchmark

The [Open Graph Benchmark (OGB)](https://ogb.stanford.edu/docs/home/) provides
realistic graph datasets with standardized splits and evaluators for machine
learning on graphs. This project uses **OGBG-MolHIV**, a molecular property
prediction task: predict whether a molecule inhibits HIV replication.

### Baseline

The baseline converts each molecule’s SMILES representation into a 2048-bit
Morgan fingerprint with radius 2, then trains logistic regression. It uses
OGB’s official scaffold split and ROC-AUC evaluator, averaging results over ten
seeds. In this session, explore the baseline and its Hiraku records, then try a
well-described, reproducible experiment.

## Session map

| Step | What you’ll do |
| --- | --- |
| **1 · Browse records** | Understand the project goal and baseline hypothesis |
| **2 · Inspect runs** | Compare existing results on the leaderboard |
| **3 · Try an experiment** | Form a hypothesis and make a focused change |
| **4 · Review results** | Compare metrics and interpret what they support |

## 1 - Browse existing records

In a Renku session, open a terminal and inspect the project’s Hiraku records:

```bash
hiraku record list
hiraku record show open-graph-benchmark
hiraku record show open-graph-benchmark/ogbg-molhiv-baseline
```

The task record describes the overall goal. The child experiment record holds
the baseline hypothesis and evaluation metric.

## 2 - Find previous runs on the leaderboard

The project has a default MLflow leaderboard visible at https://standings-antiques-look-plots.trycloudflare.com/#/?workspace=ddeq4clusters .
List available leaderboards and inspect existing runs:

```bash
hiraku leaderboard list
hiraku leaderboard runs
hiraku leaderboard runs --record open-graph-benchmark/ogbg-molhiv-baseline
```

Use the leaderboard to see what has already been run and compare metrics and
parameters. The default leaderboard ranks runs by validation ROC-AUC mean and
standard deviation.

## 3 - Try an experiment

Start with a question about the baseline. For example:

> What happens to validation ROC-AUC if you change the fingerprint radius or
> size?

Before running, inspect the relevant records and previous runs. Describe your
experiment in a Hiraku record: state the hypothesis, the change you plan to make,
and how you’ll evaluate the result. Then launch a tracked run against that
record and compare it with the baseline.

## 4 - Use a coding agent

You can explore the project through an agent running in the repository
directory. Start with a specific task, such as:

> Inspect the Hiraku records and leaderboard, summarize the baseline, and suggest
> one small experiment.

### Codex

Launch Codex in this Renku environment with:

```bash
codex --yolo
```

For optional alphaXiv literature search, create an API key at
[alphaXiv API Keys](https://www.alphaxiv.org/settings/api-keys). Before
launching an agent, export it in the shell (replace the placeholder):

```bash
export ALPHAXIV_API_KEY="<your-alphaXiv-api-key>"
```

Then add alphaXiv to Codex:

```bash
codex mcp add alphaxiv --url https://api.alphaxiv.org/mcp/v1 \
  --bearer-token-env-var ALPHAXIV_API_KEY
codex mcp list
```

Restart Codex if it is already running.

### Claude Code

Launch Claude Code with:

```bash
claude --dangerously-skip-permissions
```

With `ALPHAXIV_API_KEY` set in the shell, add alphaXiv to Claude Code:

```bash
claude mcp add --transport http --scope user alphaxiv \
  https://api.alphaxiv.org/mcp/v1 \
  --header 'Authorization: Bearer ${ALPHAXIV_API_KEY}'
claude mcp list
```

Restart Claude Code if it is already running.

### Pi

Start Pi with:

```bash
pi
```

> To use Pi with SDSC LLMs, run `/login`, select SDSC LLM, then complete the
> OAuth flow.

With `ALPHAXIV_API_KEY` set in the shell, add alphaXiv to Pi:

```bash
pi mcp add alphaxiv --url https://api.alphaxiv.org/mcp/v1 \
  --bearer-token-env-var ALPHAXIV_API_KEY
pi mcp list
```

Restart Pi if it is already running.

The API key is read from the session environment; keep it out of the command
and config files. The API key uses a bearer header and skips OAuth. See the
[alphaXiv MCP guide](https://www.alphaxiv.org/docs/mcp) for details. Ask the
agent to use alphaXiv to discover and read papers when you want to try the
bundled literature-review skill.

### Working with an agent

Give the agent a clear task and scope, for example:

> Read the Hiraku records and inspect existing leaderboard runs. Suggest one
> experiment and explain the tradeoffs.

Ask the agent to inspect the records and previous runs first. Once you choose an
experiment, have it explain its proposed changes, then launch a tracked run
against the experiment record. Review the metrics yourself and ask the agent to
help interpret what the results support.

You can also mix manual and agent-assisted steps: explore records with the CLI,
ask an agent to suggest a change, then run and analyze it yourself.
