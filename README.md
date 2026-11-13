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
The Renku Linux image and runtime services still need validation after push/build.

## Renku build from code

Target project: <https://renkulab.io/p/sdsc/hiraku-all-hands>.
After committing and pushing this branch, add/select a launcher with:

| Setting | Value |
| --- | --- |
| Repository | `https://github.com/SwissDataScienceCenter/hiraku-all-hands.git` |
| Revision | `kirschnj/ogb-benchmark` |
| Image source | Build from code |
| Builder | Python |
| Frontend | VS Code (`vscodium`) |
| Context directory | `.` |
| Platform | `linux/amd64` |

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
cd /home/renku/work/hiraku-all-hands
git switch kirschnj/ogb-benchmark
uv run --locked --no-sync ogbg-molhiv.py
```

`--no-sync` reuses the dependencies already built into the image and inherited by
Renku's session virtual environment. A normal `uv run` can reinstall inherited
packages into the writable environment, duplicating the image's dependencies.
Use `uv sync --locked` when intentionally changing the session dependencies.
Rebuild after dependency/build configuration
changes; code-only changes require a fresh checkout/session rather than a rebuild.

### Session tools and SSH

As in the upstream base, the startup hook installs Node 24, Pi, Claude Code,
Codex, AWS CLI and iroh-ssh at runtime, then configures persistent agent directories
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
`codex --version`, `aws --version`, and `iroh-ssh --help`. Authenticate interactively
with `rnk login`; in Pi use `/login` and choose SDSC LLM (OIDC).
No credentials are included in the image or repository.

## Upstream attribution

`project.toml`, `init.d/setup.sh`, and `sdsc-llm.ts` are adapted/copied from
[renku-docker-base](https://gitlab.datascience.ch/kirschnj/renku-docker-base),
revision `e76851096c514e9bf04188887aaabd96000658d1`.
Changes adapt the project metadata/build inputs to uv, add the user-local rnk
installer, and allow non-SSH tooling to initialize without mounted secrets.
