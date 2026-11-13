"""Run the OGBG-MolHIV example with ``uv run --locked main.py``."""

from pathlib import Path
import runpy


def main():
    runpy.run_path(str(Path(__file__).with_name("ogbg-molhiv.py")), run_name="__main__")


if __name__ == "__main__":
    main()
