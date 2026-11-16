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

The project has a default leaderboard connected to its hosted MLflow instance.
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

### Codex, Claude Code, or Pi

In this Renku environment, launch Codex with `--yolo`:

```bash
codex --yolo
```

This starts Codex without interactive approval prompts. Give it a clear task and
scope, for example:

> Read the Hiraku records and inspect existing leaderboard runs. Suggest one
> experiment and explain the tradeoffs.

You can start Claude Code with:

```bash
claude --dangerously-skip-permissions
```

or Pi with:

```bash
pi
```

Ask the agent to inspect the records and previous runs first. Once you choose an
experiment, have it explain its proposed changes, then launch a tracked run
against the experiment record. Review the metrics yourself and ask the agent to
help interpret what the results support.

You can also mix manual and agent-assisted steps: explore records with the CLI,
ask an agent to suggest a change, then run and analyze it yourself. The aim is to
learn how Hiraku’s records, project code, tracked runs, and leaderboard fit
together.
