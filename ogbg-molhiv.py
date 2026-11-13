"""Run with: uv run --locked ogbg-molhiv.py

The first run downloads the OGB dataset to scratch/ogb. The ten-seed scores
use OGB's scaffold split and evaluator, as on the public leaderboard:
https://ogb.stanford.edu/docs/leader_graphprop/
"""

from pathlib import Path

import numpy as np
import pandas as pd
from ogb.graphproppred import Evaluator, GraphPropPredDataset
from rdkit import Chem
from rdkit.Chem import rdFingerprintGenerator
from sklearn.linear_model import LogisticRegression


def main() -> None:
    root = Path(__file__).resolve().parent / "scratch" / "ogb"
    dataset = GraphPropPredDataset(name="ogbg-molhiv", root=str(root))
    splits = dataset.get_idx_split()
    evaluator = Evaluator(name="ogbg-molhiv")

    # OGB's SMILES mapping has the same row order as its graphs and labels.
    mapping = pd.read_csv(root / "ogbg_molhiv" / "mapping" / "mol.csv.gz")
    generator = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
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

    scores = {"valid": [], "test": []}
    for seed in range(10):
        model = LogisticRegression(solver="liblinear", random_state=seed, max_iter=1000)
        train = splits["train"]
        model.fit(features[train], labels[train].ravel())
        for split in scores:
            indices = splits[split]
            predictions = model.predict_proba(features[indices])[:, 1:2]
            score = evaluator.eval(
                {"y_true": labels[indices], "y_pred": predictions}
            )["rocauc"]
            scores[split].append(score)
        print(f"seed {seed}: valid={scores['valid'][-1]:.4f} "
              f"test={scores['test'][-1]:.4f}", flush=True)

    for split, values in scores.items():
        print(f"{split} ROC-AUC: {np.mean(values):.4f} ± "
              f"{np.std(values, ddof=1):.4f} (10 seeds)")


if __name__ == "__main__":
    main()
