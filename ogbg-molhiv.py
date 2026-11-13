"""Run the OGBG-MolHIV Morgan fingerprint baseline.

The first run downloads the dataset into ``scratch/ogb``. Metrics use the
official scaffold split and OGB evaluator:
https://ogb.stanford.edu/docs/leader_graphprop/

For MLflow logging, set ``MLFLOW_TRACKING_URI`` and exactly one of
``MLFLOW_EXPERIMENT_ID`` or ``MLFLOW_EXPERIMENT_NAME``. Hiraku supplies record
and job attribution variables when it launches the command.
"""

from __future__ import annotations

import argparse
import os
from collections.abc import Sequence
from pathlib import Path

import mlflow
import numpy as np
import pandas as pd
from ogb.graphproppred import Evaluator, GraphPropPredDataset
from rdkit import Chem
from rdkit.Chem import rdFingerprintGenerator
from sklearn.linear_model import LogisticRegression


def _positive_int(value: str) -> int:
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return number


def _nonnegative_int(value: str) -> int:
    number = int(value)
    if number < 0:
        raise argparse.ArgumentTypeError("must be 0 or greater")
    return number


def _at_least_two(value: str) -> int:
    number = int(value)
    if number < 2:
        raise argparse.ArgumentTypeError(
            "must be at least 2 to report sample standard deviation"
        )
    return number


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-root",
        type=Path,
        default=Path(__file__).resolve().parent / "scratch" / "ogb",
        help="OGB dataset cache directory (default: %(default)s)",
    )
    parser.add_argument(
        "--fingerprint-radius",
        type=_nonnegative_int,
        default=2,
        help="Morgan fingerprint radius (default: %(default)s)",
    )
    parser.add_argument(
        "--fingerprint-size",
        type=_positive_int,
        default=2048,
        help="Morgan fingerprint bit count (default: %(default)s)",
    )
    parser.add_argument(
        "--seeds",
        type=_at_least_two,
        default=10,
        help="number of model seeds (at least 2; default: %(default)s)",
    )
    parser.add_argument(
        "--max-iter",
        type=_positive_int,
        default=1000,
        help="logistic regression iteration limit (default: %(default)s)",
    )
    parser.add_argument(
        "--run-name",
        help="MLflow run name (default is derived from fingerprint settings)",
    )
    return parser


def _load_features(
    root: Path,
    dataset: GraphPropPredDataset,
    radius: int,
    fingerprint_size: int,
) -> tuple[np.ndarray, np.ndarray]:
    # The OGB SMILES mapping has the same row order as its graphs and labels.
    mapping = pd.read_csv(root / "ogbg_molhiv" / "mapping" / "mol.csv.gz")
    generator = rdFingerprintGenerator.GetMorganGenerator(
        radius=radius, fpSize=fingerprint_size
    )
    fingerprints = []
    for smiles in mapping["smiles"]:
        molecule = Chem.MolFromSmiles(smiles)
        if molecule is None:
            # A few structures contain unusual valences rejected by RDKit.
            molecule = Chem.MolFromSmiles(smiles, sanitize=False)
            if molecule is None:
                raise ValueError(f"Invalid SMILES in OGB mapping: {smiles!r}")
            molecule.UpdatePropertyCache(strict=False)
            Chem.GetSymmSSSR(molecule)
        fingerprints.append(generator.GetFingerprintAsNumPy(molecule))

    features = np.asarray(fingerprints, dtype=np.float32)
    labels = np.asarray([dataset[i][1] for i in range(len(dataset))]).reshape(-1, 1)
    if len(features) != len(labels):
        raise ValueError("SMILES mapping and graph labels have different lengths")
    return features, labels


def _log_metrics(
    metrics: dict[str, float],
    *,
    args: argparse.Namespace,
    tracking_uri: str,
    experiment_id: str | None,
    experiment_name: str | None,
) -> None:
    mlflow.set_tracking_uri(tracking_uri)
    if experiment_id:
        run_context = mlflow.start_run(
            experiment_id=experiment_id,
            run_name=args.run_name
            or f"ogbg-molhiv-morgan-r{args.fingerprint_radius}-s{args.seeds}",
        )
    else:
        mlflow.set_experiment(experiment_name)
        run_context = mlflow.start_run(
            run_name=args.run_name
            or f"ogbg-molhiv-morgan-r{args.fingerprint_radius}-s{args.seeds}",
        )

    tags = {
        "hiraku.record_id": os.environ.get("HIRAKU_RECORD_ID"),
        "hiraku.job_id": os.environ.get("HIRAKU_JOB_ID"),
        "hiraku.commit": os.environ.get("HIRAKU_COMMIT"),
    }
    with run_context:
        for key, value in tags.items():
            if value:
                mlflow.set_tag(key, value)
        mlflow.log_params(
            {
                "dataset": "ogbg-molhiv",
                "fingerprint": "Morgan",
                "fingerprint_radius": args.fingerprint_radius,
                "fingerprint_size": args.fingerprint_size,
                "model": "LogisticRegression",
                "solver": "liblinear",
                "max_iter": args.max_iter,
                "seeds": args.seeds,
                "split": "official scaffold",
            }
        )
        mlflow.log_metrics(metrics)


def main(argv: Sequence[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    tracking_uri = os.environ.get("MLFLOW_TRACKING_URI")
    experiment_id = os.environ.get("MLFLOW_EXPERIMENT_ID")
    experiment_name = os.environ.get("MLFLOW_EXPERIMENT_NAME")
    if not tracking_uri:
        parser.error("set MLFLOW_TRACKING_URI")
    if bool(experiment_id) == bool(experiment_name):
        parser.error(
            "set exactly one of MLFLOW_EXPERIMENT_ID or "
            "MLFLOW_EXPERIMENT_NAME"
        )

    root = args.data_root.expanduser().resolve()
    dataset = GraphPropPredDataset(name="ogbg-molhiv", root=str(root))
    splits = dataset.get_idx_split()
    evaluator = Evaluator(name="ogbg-molhiv")
    features, labels = _load_features(
        root, dataset, args.fingerprint_radius, args.fingerprint_size
    )

    scores: dict[str, list[float]] = {"valid": [], "test": []}
    train = splits["train"]
    for seed in range(args.seeds):
        model = LogisticRegression(
            solver="liblinear", random_state=seed, max_iter=args.max_iter
        )
        model.fit(features[train], labels[train].ravel())
        for split, indices in splits.items():
            if split not in scores:
                continue
            predictions = model.predict_proba(features[indices])[:, 1:2]
            score = evaluator.eval(
                {"y_true": labels[indices], "y_pred": predictions}
            )["rocauc"]
            scores[split].append(float(score))
        print(
            f"seed {seed}: valid={scores['valid'][-1]:.4f} "
            f"test={scores['test'][-1]:.4f}",
            flush=True,
        )

    metrics: dict[str, float] = {}
    for split, values in scores.items():
        mean = float(np.mean(values))
        std = float(np.std(values, ddof=1))
        metrics[f"{split}/rocauc_mean"] = mean
        metrics[f"{split}/rocauc_std"] = std
        print(f"{split} ROC-AUC: {mean:.4f} ± {std:.4f} ({args.seeds} seeds)")

    _log_metrics(
        metrics,
        args=args,
        tracking_uri=tracking_uri,
        experiment_id=experiment_id,
        experiment_name=experiment_name,
    )


if __name__ == "__main__":
    main()
