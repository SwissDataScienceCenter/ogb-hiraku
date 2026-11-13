---
type: experiment
title: OGBG-MolHIV Baseline
parent_id: open-graph-benchmark
related_to: []
summary: Ten-seed OGBG-MolHIV baseline using 2048-bit radius-2 Morgan fingerprints
  and logistic regression.
hypothesis: The Morgan fingerprint logistic regression baseline provides a reproducible
  reference ROC-AUC on OGBG-MolHIV using the official scaffold split and evaluator.
command: uv run --locked ogbg-molhiv.py
metric: ROC-AUC (validation and test; mean and sample standard deviation across 10
  seeds)
---