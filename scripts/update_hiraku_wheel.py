"""Build a pinned Hiraku wheel without changing the developer's checkout.

Requires Python 3.11+, git, uv, and ordinary Git access to the source repository.
No credentials are written to the vendored provenance or project configuration.
"""

from __future__ import annotations

import argparse
from email.parser import BytesParser
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
from urllib.parse import urlsplit
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parent.parent
REPOSITORY = "https://github.com/SwissDataScienceCenter/hiraku.git"
DEFAULT_REF = "feat/renku-api-psij-executor"


def run(*command: str, cwd: Path | None = None) -> str:
    return subprocess.run(
        command, cwd=cwd, check=True, text=True, stdout=subprocess.PIPE
    ).stdout.strip()


def update_wheel(repository: str, ref: str, root: Path = ROOT) -> dict:
    if not ref or ref.startswith("-"):
        raise ValueError("Specify a non-empty Git branch, tag, or commit")
    # Authentication belongs in Git's credential helper, never in provenance.
    parsed = urlsplit(repository)
    if parsed.scheme in {"http", "https"} and (parsed.username or parsed.password):
        raise ValueError("Use a Git credential helper, not credentials in the URL")

    destination = root / "wheels"
    manifest = destination / "hiraku-source.json"
    previous = json.loads(manifest.read_text()) if manifest.exists() else {}
    old_wheel = previous.get("wheel", "")
    if old_wheel and (Path(old_wheel).name != old_wheel or not old_wheel.startswith("hiraku-")):
        raise ValueError("Invalid previous wheel filename in provenance")
    with tempfile.TemporaryDirectory(prefix="hiraku-wheel-") as temporary:
        checkout = Path(temporary) / "source"
        checkout.mkdir()
        run("git", "init", "--quiet", str(checkout))
        run("git", "remote", "add", "origin", repository, cwd=checkout)
        run("git", "fetch", "--quiet", "--depth", "1", "origin", ref, cwd=checkout)
        run("git", "checkout", "--quiet", "--detach", "FETCH_HEAD", cwd=checkout)
        commit = run("git", "rev-parse", "HEAD", cwd=checkout)
        output = Path(temporary) / "dist"
        run("uv", "build", "--wheel", "--out-dir", str(output), str(checkout))
        wheels = list(output.glob("hiraku-*.whl"))
        if len(wheels) != 1:
            raise ValueError(f"Expected one Hiraku wheel, found {len(wheels)}")
        wheel = wheels[0]
        with ZipFile(wheel) as archive:
            metadata_paths = [n for n in archive.namelist() if n.endswith(".dist-info/METADATA")]
            if len(metadata_paths) != 1:
                raise ValueError("Wheel must contain one distribution's metadata")
            metadata = BytesParser().parsebytes(archive.read(metadata_paths[0]))
            if metadata["Name"].lower() != "hiraku":
                raise ValueError("Built wheel is not Hiraku")
        provenance = {
            "repository": repository,
            "ref": ref,
            "commit": commit,
            "version": metadata["Version"],
            "wheel": wheel.name,
            "sha256": hashlib.sha256(wheel.read_bytes()).hexdigest(),
        }
        destination.mkdir(exist_ok=True)
        target = destination / wheel.name
        paths = [root / "pyproject.toml", root / "uv.lock", manifest, target]
        backups = {p: p.read_bytes() if p.exists() else None for p in paths}
        try:
            shutil.copyfile(wheel, target)
            # --no-sync updates dependency configuration/lock without touching
            # the developer's virtualenv. Refresh also handles unchanged versions
            # whose branch snapshot produced new wheel contents.
            run("uv", "add", "--no-sync", f"./wheels/{wheel.name}", cwd=root)
            run("uv", "lock", "--refresh-package", "hiraku", cwd=root)
            manifest.write_text(json.dumps(provenance, indent=2) + "\n")
        except BaseException:
            for path, content in backups.items():
                if content is None:
                    path.unlink(missing_ok=True)
                else:
                    path.write_bytes(content)
            raise
        if old_wheel and old_wheel != wheel.name:
            # Remove only the previously recorded artifact, never arbitrary files.
            (destination / old_wheel).unlink(missing_ok=True)
    return provenance


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ref", default=DEFAULT_REF, help="Git branch, tag, or commit")
    parser.add_argument("--repository", default=REPOSITORY, help="Source Git repository")
    args = parser.parse_args()
    try:
        provenance = update_wheel(args.repository, args.ref)
    except (ValueError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"Wheel refresh failed: {error}\n")
    print(json.dumps(provenance, indent=2))
    print("Review wheels/, pyproject.toml, and uv.lock. Nothing was committed or pushed.")


if __name__ == "__main__":
    main()
