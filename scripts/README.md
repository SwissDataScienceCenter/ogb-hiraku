# Script notes

## Update the Hiraku wheel

`update-hiraku-wheel.sh` rebuilds the local Hiraku wheel snapshot from a branch,
tag, or commit in the Hiraku source repository. For example:

```bash
./scripts/update-hiraku-wheel.sh --ref release/v0.2.0
```

The helper requires Python 3.11+, Git, `uv`, and Git authentication for the
source repository. It builds from a temporary checkout and updates:

- the wheel in `wheels/`;
- `wheels/hiraku-source.json` with source ref, commit, and SHA256;
- the local wheel reference in `pyproject.toml`;
- the resolved dependency in `uv.lock`.

The wheel’s filename and package version come from the source package metadata
at the selected ref. A ref named `release/v0.2.0` does not by itself make the
wheel version `0.2.0`; the package metadata at that commit must declare that
version.

The helper does not commit or push. Review the generated wheel, provenance,
`pyproject.toml`, and `uv.lock`, then commit them together when ready.

### Sync after rebuilding the wheel

When refreshing the existing local wheel, its filename and version may stay
the same while its contents and SHA256 change. Refresh the Hiraku lock entry
after rebuilding so `uv sync` doesn't reject the wheel with a hash mismatch:

```bash
./scripts/update-hiraku-wheel.sh --ref release/v0.2.0
uv lock --upgrade-package hiraku
uv sync
```

Use the source ref you intend to build; the script's default ref may differ
from the ref recorded in `wheels/hiraku-source.json`. Confirm `uv sync`
completes, then review the wheel, provenance, `pyproject.toml`, and `uv.lock`
changes. Commit and push those files before rebuilding the Renku image so the
image build uses the updated wheel and lockfile.

If the wheel has already been rebuilt and only its hash is stale, run just:

```bash
uv lock --upgrade-package hiraku
uv sync
```
