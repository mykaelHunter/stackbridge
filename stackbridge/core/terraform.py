"""
stackbridge.core.terraform
===========================
Wraps Terraform so the CLI commands (create, destroy, status) never
shell out directly. This is the actual provisioning logic — the
commands/ layer just parses arguments and calls into here, same
pattern as core/deploy.py.

Design notes:
  - Every function takes `environment` and resolves the working
    directory itself. Nothing relies on the caller's cwd, which
    was the main gap in the original utils/terraform.py stub —
    that version ran `terraform init` wherever the CLI happened
    to be invoked from, not inside infra/environments/<env>/.
  - dev/staging/prod each load variables automatically via their
    *.auto.tfvars file — Terraform picks these up on its own, so
    nothing here needs to pass -var-file explicitly.
  - OPA policy checks (infra/policies/) run between plan and
    apply, matching the workflow established earlier in this
    project for both the CLI and CI. A policy violation blocks
    the apply — it does not just warn.
  - prod is deliberately not in VALID_ENVIRONMENTS. Provisioning
    or destroying prod from a local CLI run was an explicit
    non-goal earlier in this project; that should go through
    CI with its own approval gates, not a laptop.
"""

import json
import shutil
import subprocess
from pathlib import Path

from stackbridge.core.paths import REPO_ROOT

VALID_ENVIRONMENTS = ["dev", "staging"]

ENVIRONMENTS_ROOT = REPO_ROOT / "infra" / "environments"
POLICIES_DIR = REPO_ROOT / "infra" / "policies"


class TerraformError(Exception):
    """Raised when a Terraform or policy step fails. Carries the
    human-readable reason so commands/ can print it without
    needing to know subprocess internals."""


def _environment_dir(environment: str) -> Path:
    if environment not in VALID_ENVIRONMENTS:
        raise TerraformError(
            f"Unknown environment '{environment}'. "
            f"Valid options: {', '.join(VALID_ENVIRONMENTS)}. "
            f"(prod is intentionally excluded from CLI provisioning — "
            f"use the CI pipeline for prod.)"
        )

    env_dir = ENVIRONMENTS_ROOT / environment
    if not env_dir.exists():
        raise TerraformError(
            f"Environment directory not found: {env_dir}\n"
            f"Has infra/environments/{environment}/ been created?"
        )

    return env_dir


def _check_terraform_installed() -> None:
    if shutil.which("terraform") is None:
        raise TerraformError(
            "'terraform' not found in PATH. "
            "Install: https://developer.hashicorp.com/terraform/install"
        )


def _check_conftest_installed() -> bool:
    """conftest (OPA policy check) is treated as optional but
    strongly recommended — same posture as the rest of this
    project. Returns False (with no exception) if missing, so
    the caller can decide whether to warn and continue."""
    return shutil.which("conftest") is not None


def _run(cmd: list[str], cwd: Path, capture: bool = False) -> subprocess.CompletedProcess:
    if capture:
        return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    return subprocess.run(cmd, cwd=cwd, text=True)


def terraform_init(environment: str) -> None:
    _check_terraform_installed()
    env_dir = _environment_dir(environment)

    result = _run(["terraform", "init", "-input=false"], cwd=env_dir)
    if result.returncode != 0:
        raise TerraformError(f"terraform init failed for environment '{environment}'")


def terraform_plan(environment: str, destroy: bool = False) -> Path:
    """Runs terraform plan and returns the path to the saved
    plan file. Caller decides whether to run the policy check
    and apply, or just inspect the plan."""
    _check_terraform_installed()
    env_dir = _environment_dir(environment)

    plan_file = env_dir / "tfplan.binary"
    cmd = ["terraform", "plan", "-input=false", f"-out={plan_file.name}"]
    if destroy:
        cmd.insert(2, "-destroy")

    result = _run(cmd, cwd=env_dir)
    if result.returncode != 0:
        raise TerraformError(f"terraform plan failed for environment '{environment}'")

    return plan_file


def run_policy_check(environment: str, plan_file: Path) -> None:
    """Exports the saved plan to JSON and runs conftest against
    infra/policies/. Raises TerraformError on any policy denial
    — this is a hard gate, not a warning, matching how the OPA
    policies were designed to behave in CI.
    """
    env_dir = _environment_dir(environment)

    if not _check_conftest_installed():
        print(
            "  conftest not installed — skipping OPA policy check. "
            "Install: https://www.conftest.dev/install/"
        )
        return

    plan_json = env_dir / "tfplan.json"
    show_result = _run(
        ["terraform", "show", "-json", plan_file.name],
        cwd=env_dir,
        capture=True,
    )
    if show_result.returncode != 0:
        raise TerraformError("Could not export plan to JSON for policy check")

    plan_json.write_text(show_result.stdout)

    conftest_result = _run(
        [
            "conftest", "test", plan_json.name,
            "--policy", str(POLICIES_DIR),
            "--output", "json",
        ],
        cwd=env_dir,
        capture=True,
    )

    try:
        output = json.loads(conftest_result.stdout)
    except json.JSONDecodeError:
        # conftest prints non-JSON on some error paths (e.g. no
        # policies found) — don't silently pass in that case.
        raise TerraformError(
            f"Could not parse conftest output:\n{conftest_result.stdout}\n{conftest_result.stderr}"
        )

    failures = [r for r in output if r.get("failures")]
    warnings = [r for r in output if r.get("warnings")]

    for w in warnings:
        for warning in w.get("warnings", []):
            print(f"  [policy warning] {warning}")

    if failures:
        messages = []
        for f in failures:
            for failure in f.get("failures", []):
                messages.append(failure)
        raise TerraformError(
            "OPA policy check failed — refusing to apply:\n"
            + "\n".join(f"  - {m}" for m in messages)
        )


def terraform_apply(environment: str, plan_file: Path) -> None:
    _check_terraform_installed()
    env_dir = _environment_dir(environment)

    result = _run(["terraform", "apply", "-input=false", plan_file.name], cwd=env_dir)
    if result.returncode != 0:
        raise TerraformError(f"terraform apply failed for environment '{environment}'")


def terraform_destroy(environment: str) -> None:
    """Plans a destroy, then applies it. Unlike terraform_provision
    below, this does not run the OPA policy check — the policies
    in this project validate that resources being CREATED meet
    security/tagging standards, which is meaningless for a
    destroy plan (there's nothing left to tag or secure).
    """
    _check_terraform_installed()
    env_dir = _environment_dir(environment)

    plan_file = terraform_plan(environment, destroy=True)

    result = _run(["terraform", "apply", "-input=false", plan_file.name], cwd=env_dir)
    if result.returncode != 0:
        raise TerraformError(f"terraform destroy failed for environment '{environment}'")


def terraform_outputs(environment: str) -> dict:
    _check_terraform_installed()
    env_dir = _environment_dir(environment)

    result = _run(["terraform", "output", "-json"], cwd=env_dir, capture=True)
    if result.returncode != 0:
        # No outputs yet is not necessarily an error — environment
        # may simply not be provisioned. Return empty rather than raise.
        return {}

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {}


def terraform_resources(environment: str) -> list[str]:
    _check_terraform_installed()
    env_dir = _environment_dir(environment)

    result = _run(["terraform", "state", "list"], cwd=env_dir, capture=True)
    if result.returncode != 0:
        return []

    return [line for line in result.stdout.strip().split("\n") if line]


def provision(environment: str) -> dict:
    """Full create flow: init -> plan -> policy check -> apply.
    This is the function commands/create.py should call — it's
    the orchestration the original stub never had.
    """
    terraform_init(environment)
    plan_file = terraform_plan(environment)
    run_policy_check(environment, plan_file)
    terraform_apply(environment, plan_file)
    return terraform_outputs(environment)
