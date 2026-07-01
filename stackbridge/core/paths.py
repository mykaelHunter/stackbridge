"""
stackbridge.core.paths
========================
Single source of truth for locating the repository root.

Why this exists:
  Every module that needs the repo root used to compute it as
  `Path(__file__).resolve().parents[N]` — a fixed depth climb
  from wherever this source file happens to live. That works
  when running directly from a cloned repo, but breaks under
  `pip install -e .`: depending on setuptools version and how
  the editable install resolves imports, __file__ can report a
  path through .venv/lib/pythonX/site-packages/ instead of the
  actual working tree. The depth-climb then lands inside
  site-packages and never finds infra/, services/, etc.

  Fix: don't derive the root from __file__ at all. Walk upward
  from the current working directory looking for a marker file
  that only exists at the real repo root (stackbridge.yaml).
  This is the same strategy git, npm, and poetry use to find
  "project root" — it works identically whether the package was
  pip installed, installed editable, or just run from a clone,
  because it never trusts where the installed code physically
  sits on disk.

  Trade-off: this means the CLI must still be invoked from
  somewhere inside the repo tree (anywhere inside it — repo
  root, services/<name>/, infra/environments/dev/, all work).
  Running it from a completely unrelated directory will raise
  RepoRootNotFound with a clear message instead of silently
  resolving to the wrong place, which is the failure mode this
  replaces.
"""

from pathlib import Path

MARKER_FILE = "stackbridge.yaml"


class RepoRootNotFound(Exception):
    """Raised when no stackbridge.yaml is found walking up from cwd."""


def find_repo_root(start: Path | None = None) -> Path:
    """
    Walk upward from `start` (defaults to cwd) until a directory
    containing stackbridge.yaml is found. Returns that directory.
    """
    current = (start or Path.cwd()).resolve()

    for candidate in [current, *current.parents]:
        if (candidate / MARKER_FILE).exists():
            return candidate

    raise RepoRootNotFound(
        f"Could not locate '{MARKER_FILE}' in '{current}' or any parent "
        f"directory. Run this command from inside the stackbridge repo."
    )


# Resolved once at import time. If this raises, it raises
# immediately and loudly on first use rather than silently
# pointing at the wrong directory — same intent as before, but
# now it actually fails closed instead of failing open.
REPO_ROOT = find_repo_root()
