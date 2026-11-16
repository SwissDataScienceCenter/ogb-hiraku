# Hiraku All Hands benchmark

OGBG-MolHIV baseline: radius-2 Morgan fingerprints (2048 bits), logistic
regression, the official scaffold split and OGB ROC-AUC evaluator, over ten seeds.

## Local use

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), then run:

```bash
uv sync --locked
uv run --locked ogbg-molhiv.py
# Equivalent convenience entry point:
uv run --locked main.py
```

Python 3.12 is selected in `.python-version`. Dependencies are declared in
`pyproject.toml` and resolved in `uv.lock`. The existing NumPy <2 and PyTorch <2.6
constraints are retained for OGB 1.3.6 compatibility; its cached dataset loader
uses `torch.load` without opting out of the newer weights-only default.
Linux uses the official PyTorch CPU wheels: this baseline does not use CUDA.
The first run downloads the dataset into `scratch/ogb/` inside this repository.
Dataset downloads, virtual environments, agent state, and credentials are ignored.

Validated locally with Python 3.12.12, NumPy 1.26.4, PyTorch 2.5.1,
RDKit 2026.9.2 and scikit-learn 1.9.1: validation ROC-AUC **0.7758**,
test ROC-AUC **0.7289** (ten seeds; standard deviations round to 0.0000).
Both the initial dataset download and cached-dataset run completed successfully.
The Renku Linux CPU image also completed the full ten-seed benchmark with the
same scores; Pi, Claude Code, Codex, rnk, and SDSC model discovery were
verified in the VS Code session. SSH requires the optional mounted key secrets.

## Renku build from code

Target project: <https://renkulab.io/p/sdsc/ogb-hiraku-demo>.
After committing and pushing this branch, add/select a launcher with:

| Setting | Value |
| --- | --- |
| Repository | `https://github.com/SwissDataScienceCenter/ogb-hiraku.git` |
| Revision | `main` |
| Image source | Build from code |
| Builder | Python |
| Frontend | VS Code (`vscodium`) |
| Context directory | `.` |
| Platform | `linux/amd64` |
| Launcher environment variable | `UV_PROJECT_ENVIRONMENT=/home/renku/work/.venv` |

Select an accessible CPU resource class explicitly; start with at least 2 CPUs
and 8 GiB RAM for the benchmark plus editor and agents. Use a larger class if
running multiple agents. The available class IDs must be checked in Renku.

Renku's Python builder installs the locked uv dependencies. `project.toml`
also includes the base environment's Debian packages, startup hook and SDSC LLM
extension. Repository source is checked out at session start under
`/home/renku/work/hiraku-all-hands`; it is not baked into the environment image.
Renku initially checks out the repository's default branch independently of the
image's build revision. In a fresh session terminal run:

```bash
cd /home/renku/work/ogb-hiraku
python ogbg-molhiv.py
# Equivalently, use uv without syncing the inherited environment:
uv run --locked --no-sync ogbg-molhiv.py
```

Renku provides a writable session virtualenv at `/home/renku/work/.venv` that
inherits the image's packages.

**uv limitation:** inherited packages are importable, but uv's installer does not
count them as installed. Full `uv sync`, syncing `uv add`, and plain `uv run` can
therefore reinstall image packages into the session, consuming extra disk/memory.
Use plain `python` or `uv run --no-sync` with the built environment in Renku.

For incremental session installs with dependency resolution, use
`python -m pip install <package>`: pip recognizes inherited packages and puts
additions in the writable virtualenv.

### Hiraku release wheel

`wheels/` contains the built Hiraku wheel and `hiraku-source.json`, which records
its source ref, exact commit and SHA256. The default source is
`feat/renku-api-psij-executor` from the private Hiraku repository. The committed
wheel is a snapshot: it does not follow branch changes at image-build time.
Renku installs the local wheel from `pyproject.toml`/`uv.lock`, so the image build
does not need credentials to fetch a second private repository. Hiraku's regular
dependencies are included in the image too.

To refresh the snapshot from a branch, tag, or commit:

```bash
./scripts/update-hiraku-wheel.sh --ref feat/renku-api-psij-executor
# Or select a release tag:
./scripts/update-hiraku-wheel.sh --ref v0.1.1
```

The helper needs Python 3.11+, git, uv and normal Git authentication. It builds in
a temporary checkout, leaving any existing Hiraku checkout untouched. It updates
the wheel, provenance, project dependency and lockfile without syncing your
environment, committing, or pushing. Review and commit those files together.
`--repository` can select a different source repository when needed.

The image uses this wheel independently of the branch checked out in the sibling
`/home/renku/work/hiraku` directory. No editable path or `PYTHONPATH` override is
needed. Refresh the wheel and rebuild to select a different Hiraku revision.

To install a different wheel into the writable session environment without
reinstalling its dependencies, use
`uv pip install --python "$VIRTUAL_ENV/bin/python" --no-deps /path/to/package.whl`.
Use `python -m pip install /path/to/package.whl` if its requirements also need to
be resolved against inherited packages. Keep local session experiments separate
from the demo's reproducible wheel and lockfile.

### Session tools and SSH

As in the upstream base, the startup hook installs Node 24, Pi, Claude Code,
Codex and iroh-ssh at runtime, then configures persistent agent directories
and the Pi SDSC LLM OAuth extension. It additionally installs Renku CLI `rnk`
v0.7.2 from its official Linux release into `$RENKU_MOUNT_DIR/.local/bin`, without
sudo or Python dependencies. Existing executables are reused on subsequent starts.
These installations need outbound network access and can delay the first launch.
Optional setup failures are logged without blocking the editor.
Node and npm come from NVM's Node 24 installation; the redundant Debian Node/npm
packages are omitted because their relocated buildpack paths caused Node to abort.

For SSH, configure Renku session secret files `authorized_keys` and
`ssh_host_ed25519_key`. Optionally provide `irohssh_ed25519` and
`irohssh_ed25519.pub` for a persistent tunnel identity. Never commit private keys.
Without SSH secrets, the other tools still initialize. After startup, use
`iroh-ssh info` for connection details. See the
[upstream SSH instructions](https://gitlab.datascience.ch/kirschnj/renku-docker-base).

In a session terminal, verify `rnk --help`, `pi --version`, `claude --version`,
`codex --version` and `iroh-ssh --help`. Authenticate interactively
with `rnk login`; in Pi use `/login` and choose SDSC LLM (OIDC).
No credentials are included in the image or repository.

## Upstream attribution

`project.toml`, `init.d/setup.sh`, and `sdsc-llm.ts` are adapted/copied from
[renku-docker-base](https://gitlab.datascience.ch/kirschnj/renku-docker-base),
revision `e76851096c514e9bf04188887aaabd96000658d1`.
Changes adapt the project metadata/build inputs to uv, add the user-local rnk
installer, and allow non-SSH tooling to initialize without mounted secrets.
