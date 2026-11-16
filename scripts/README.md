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
