# Hiraku Open Graph Benchmark Demo

Explore prior runs and test a hypothesis with the Hiraku CLI or a coding agent.
The [OGBG-MolHIV benchmark](https://ogb.stanford.edu/docs/home/) asks whether a
molecule inhibits HIV replication. The baseline trains logistic regression on
2048-bit Morgan fingerprints (radius 2) and reports ROC-AUC across 10 seeds
using OGB’s official scaffold split and evaluator.

## Inspect the baseline

```bash
hiraku record list
hiraku record show open-graph-benchmark
hiraku record show open-graph-benchmark/ogbg-molhiv-baseline
hiraku leaderboard list
hiraku leaderboard runs
```

The records describe the project goal and baseline hypothesis. The default
leaderboard shows validation ROC-AUC mean and standard deviation.

## Try an experiment

Change one setting, such as fingerprint radius or size. Record your hypothesis,
the proposed change, and your evaluation metric in Hiraku. Launch a tracked run
against that record, then compare validation ROC-AUC with the baseline.

## Use a coding agent

From the repository directory, launch your preferred agent.

| Agent | Command |
| --- | --- |
| Codex | `codex` |
| Claude Code | `claude` |
| Pi | `pi` |

To use Pi with SDSC LLMs, run `/login`, select SDSC LLM, and complete OAuth. Additional setup instructions are in the [SDSC LLM docs](https://swissdatasciencecenter.github.io/llm-docs/).

Give the agent this prompt.

```text
Review the Hiraku records and leaderboard, then summarize the baseline.
Create an experiment record with one proposed change, a falsifiable hypothesis,
the metric, and criteria for interpreting the result.
Implement the change and complete a tracked run under baseline conditions.
Compare the results with the baseline and link the record and run.
```

### Agentic literature review

[Create an alphaXiv API key](https://www.alphaxiv.org/settings/api-keys) and
export it in the shell before launching the agent.

```bash
export ALPHAXIV_API_KEY="<your-alphaXiv-api-key>"
```

Run the commands for your agent.

```bash
# Codex
codex mcp add alphaxiv --url https://api.alphaxiv.org/mcp/v1 \
  --bearer-token-env-var ALPHAXIV_API_KEY
codex mcp list

# Claude Code
claude mcp add --transport http --scope user alphaxiv \
  https://api.alphaxiv.org/mcp/v1 \
  --header 'Authorization: Bearer ${ALPHAXIV_API_KEY}'
claude mcp list

# Pi
pi mcp add alphaxiv --url https://api.alphaxiv.org/mcp/v1 \
  --bearer-token-env-var ALPHAXIV_API_KEY
pi mcp list
```

Restart the agent if it’s already running. To try the literature-review
skill, ask the agent to find and read papers using alphaXiv. See the
[alphaXiv MCP guide](https://www.alphaxiv.org/docs/mcp) for details.
