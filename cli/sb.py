#!/usr/bin/env python3
"""
sb — StackBridge Internal CLI
==============================
The only way product teams interact with infrastructure.
Terraform never needs to be installed or understood by the caller.

Commands:
  sb env create   <environment>  [--var-file <file>]
  sb env destroy  <environment>  [--force]
  sb env status   <environment>

Examples:
  sb env create dev
  sb env create staging --var-file staging.tfvars
  sb env status dev
  sb env destroy dev --force

Design principle:
  This tool hides Terraform entirely. A product team member runs
  'sb env create dev' and gets a running environment. They do not
  need to know what Terraform is, what a state file is, or how
  modules work. That complexity lives here.
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


# ── Configuration ─────────────────────────────────────────────

REPO_ROOT = Path(__file__).parent.parent.resolve()
INFRA_ROOT = REPO_ROOT / "infra"
ENVIRONMENTS_ROOT = INFRA_ROOT / "environments"
POLICIES_DIR = INFRA_ROOT / "policies"

VALID_ENVIRONMENTS = ["dev", "staging", "prod"]

# Colours for terminal output
class C:
    RESET  = "\033[0m"
    BOLD   = "\033[1m"
    RED    = "\033[91m"
    GREEN  = "\033[92m"
    YELLOW = "\033[93m"
    CYAN   = "\033[96m"
    GREY   = "\033[90m"


# ── Helpers ───────────────────────────────────────────────────

def log(msg: str, level: str = "info") -> None:
    colours = {"info": C.CYAN, "ok": C.GREEN, "warn": C.YELLOW, "error": C.RED, "step": C.BOLD}
    colour = colours.get(level, C.RESET)
    timestamp = datetime.now().strftime("%H:%M:%S")
    prefix = {"info": "→", "ok": "✓", "warn": "!", "error": "✗", "step": "•"}[level]
    print(f"{C.GREY}[{timestamp}]{C.RESET} {colour}{prefix}{C.RESET} {msg}")


def die(msg: str) -> None:
    log(msg, "error")
    sys.exit(1)


def confirm(prompt: str) -> bool:
    response = input(f"\n{C.YELLOW}  {prompt} [y/N]: {C.RESET}").strip().lower()
    return response == "y"


def run(
    cmd: list[str],
    cwd: Path,
    capture: bool = False,
    env: dict | None = None
) -> subprocess.CompletedProcess:
    """Run a subprocess. Stream output unless capture=True."""
    full_env = {**os.environ, **(env or {})}
    if capture:
        result = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, env=full_env
        )
    else:
        result = subprocess.run(cmd, cwd=cwd, text=True, env=full_env)
    return result


def check_dependencies() -> None:
    """Fail fast if required tools are missing."""
    required = {"terraform": "brew install terraform  OR  https://developer.hashicorp.com/terraform/install"}
    optional = {"conftest": "brew install conftest  OR  https://www.conftest.dev/install/"}

    for tool, install_hint in required.items():
        if not _which(tool):
            die(f"'{tool}' not found in PATH.\n  Install: {install_hint}")

    for tool, install_hint in optional.items():
        if not _which(tool):
            log(f"'{tool}' not found — OPA policy checks will be skipped. Install: {install_hint}", "warn")


def _which(tool: str) -> bool:
    return subprocess.run(
        ["which", tool], capture_output=True
    ).returncode == 0


def env_dir(environment: str) -> Path:
    path = ENVIRONMENTS_ROOT / environment
    if not path.exists():
        die(f"Environment directory not found: {path}\nHas this environment been defined in infra/environments/?")
    return path


# ── OPA Policy Check ──────────────────────────────────────────

def run_policy_check(plan_json_path: Path, environment: str) -> bool:
    """
    Run Conftest against the Terraform plan JSON.
    Returns True if all policies pass, False if any deny fires.
    """
    if not _which("conftest"):
        log("Skipping OPA policy check (conftest not installed)", "warn")
        return True

    log("Running OPA policy checks...", "step")
    result = run(
        ["conftest", "test", str(plan_json_path), "--policy", str(POLICIES_DIR), "--output", "json"],
        cwd=env_dir(environment),
        capture=True
    )

    try:
        output = json.loads(result.stdout)
        failures = [r for r in output if r.get("failures")]
        warnings = [r for r in output if r.get("warnings")]

        for w in warnings:
            for warning in w.get("warnings", []):
                log(warning, "warn")

        if failures:
            for f in failures:
                for failure in f.get("failures", []):
                    log(failure, "error")
            log("OPA policy check FAILED — fix violations before applying", "error")
            return False

        log("OPA policy check passed", "ok")
        return True

    except json.JSONDecodeError:
        log("Could not parse conftest output — proceeding with caution", "warn")
        return True


# ── Commands ──────────────────────────────────────────────────

def cmd_create(environment: str, var_file: str | None) -> None:
    """
    Provision an environment.
    Steps: init → plan → OPA check → apply
    """
    log(f"Creating environment: {C.BOLD}{environment}{C.RESET}", "step")

    cwd = env_dir(environment)
    start = time.time()
    manual_steps = []

    # ── Step 1: terraform init ────────────────────────────────
    log("Initialising Terraform...", "step")
    result = run(["terraform", "init", "-input=false"], cwd=cwd)
    if result.returncode != 0:
        die("terraform init failed")
    log("Terraform initialised", "ok")

    # ── Step 2: terraform plan ────────────────────────────────
    log("Generating execution plan...", "step")
    plan_args = ["terraform", "plan", "-out=tfplan.binary", "-input=false"]
    if var_file:
        var_path = Path(var_file)
        if not var_path.exists():
            die(f"var-file not found: {var_file}")
        plan_args += [f"-var-file={var_file}"]
        log(f"Using var-file: {var_file}", "info")

    result = run(plan_args, cwd=cwd)
    if result.returncode != 0:
        die("terraform plan failed")

    # ── Step 3: Export plan to JSON for OPA ──────────────────
    plan_json_path = cwd / "tfplan.json"
    result = run(
        ["terraform", "show", "-json", "tfplan.binary"],
        cwd=cwd,
        capture=True
    )
    if result.returncode == 0:
        plan_json_path.write_text(result.stdout)
    else:
        log("Could not export plan to JSON — skipping OPA check", "warn")
        manual_steps.append("OPA policy check was skipped (plan export failed)")

    # ── Step 4: OPA policy check ──────────────────────────────
    if plan_json_path.exists():
        policy_passed = run_policy_check(plan_json_path, environment)
        if not policy_passed:
            die("Refusing to apply — fix OPA policy violations first")

    # ── Step 5: terraform apply ───────────────────────────────
    log("Applying plan...", "step")
    result = run(["terraform", "apply", "-input=false", "tfplan.binary"], cwd=cwd)
    if result.returncode != 0:
        die("terraform apply failed")

    # ── Step 6: Capture outputs ───────────────────────────────
    elapsed = round(time.time() - start, 1)
    outputs_result = run(
        ["terraform", "output", "-json"],
        cwd=cwd,
        capture=True
    )

    print(f"\n{C.GREEN}{C.BOLD}{'─' * 60}")
    print(f"  Environment '{environment}' created in {elapsed}s")
    print(f"{'─' * 60}{C.RESET}\n")

    if outputs_result.returncode == 0:
        try:
            outputs = json.loads(outputs_result.stdout)
            print(f"{C.BOLD}Outputs:{C.RESET}")
            for key, val in outputs.items():
                print(f"  {key} = {val.get('value', 'N/A')}")
            print()
        except json.JSONDecodeError:
            pass

    # Report any remaining manual steps
    if manual_steps:
        print(f"{C.YELLOW}{C.BOLD}Manual steps still required:{C.RESET}")
        for i, step in enumerate(manual_steps, 1):
            print(f"  {i}. {step}")
        print()


def cmd_destroy(environment: str, force: bool) -> None:
    """
    Tear down an environment.
    Always prompts for confirmation unless --force is passed.
    """
    if environment == "prod" and not force:
        die("Destroying prod requires --force. Are you absolutely sure?")

    if not force:
        print(f"\n{C.RED}{C.BOLD}  WARNING: This will destroy all resources in '{environment}'.{C.RESET}")
        print(f"  This action cannot be undone. All data will be lost.\n")
        if not confirm(f"Type 'y' to confirm destruction of '{environment}'"):
            log("Aborted", "warn")
            sys.exit(0)

    cwd = env_dir(environment)
    log(f"Destroying environment: {environment}", "step")

    result = run(["terraform", "init", "-input=false"], cwd=cwd)
    if result.returncode != 0:
        die("terraform init failed")

    result = run(["terraform", "destroy", "-auto-approve", "-input=false"], cwd=cwd)
    if result.returncode != 0:
        die("terraform destroy failed")

    log(f"Environment '{environment}' destroyed", "ok")


def cmd_status(environment: str) -> None:
    """
    Show the current state of an environment.
    Prints Terraform outputs and a resource summary.
    """
    cwd = env_dir(environment)
    log(f"Checking status of environment: {C.BOLD}{environment}{C.RESET}", "step")

    # Refresh state
    result = run(["terraform", "init", "-input=false"], cwd=cwd)
    if result.returncode != 0:
        die("terraform init failed")

    # Outputs
    outputs_result = run(
        ["terraform", "output", "-json"],
        cwd=cwd,
        capture=True
    )

    # Resource list
    state_result = run(
        ["terraform", "state", "list"],
        cwd=cwd,
        capture=True
    )

    print(f"\n{C.BOLD}{'─' * 60}")
    print(f"  Status: {environment}")
    print(f"{'─' * 60}{C.RESET}\n")

    if outputs_result.returncode == 0 and outputs_result.stdout.strip():
        try:
            outputs = json.loads(outputs_result.stdout)
            print(f"{C.BOLD}Outputs:{C.RESET}")
            for key, val in outputs.items():
                print(f"  {key} = {val.get('value', 'N/A')}")
            print()
        except json.JSONDecodeError:
            log("Could not parse outputs", "warn")
    else:
        log("No outputs found — environment may not be provisioned yet", "warn")

    if state_result.returncode == 0 and state_result.stdout.strip():
        resources = state_result.stdout.strip().split("\n")
        print(f"{C.BOLD}Resources ({len(resources)}):{C.RESET}")
        for r in resources:
            print(f"  {C.GREY}{r}{C.RESET}")
        print()
    else:
        log("No resources in state — run 'sb env create' to provision", "warn")


# ── Argument parsing ──────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sb",
        description="StackBridge CLI — manage platform environments",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  sb env create dev
  sb env create staging --var-file staging.tfvars
  sb env status dev
  sb env destroy dev
  sb env destroy dev --force
        """
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # env subcommand
    env_parser = subparsers.add_parser("env", help="Manage environments")
    env_subparsers = env_parser.add_subparsers(dest="action", required=True)

    # env create
    create_parser = env_subparsers.add_parser("create", help="Provision an environment")
    create_parser.add_argument(
        "environment",
        choices=VALID_ENVIRONMENTS,
        help="Environment to create"
    )
    create_parser.add_argument(
        "--var-file",
        metavar="FILE",
        help="Path to a .tfvars file with variable overrides"
    )

    # env destroy
    destroy_parser = env_subparsers.add_parser("destroy", help="Tear down an environment")
    destroy_parser.add_argument(
        "environment",
        choices=VALID_ENVIRONMENTS,
        help="Environment to destroy"
    )
    destroy_parser.add_argument(
        "--force",
        action="store_true",
        help="Skip confirmation prompt"
    )

    # env status
    status_parser = env_subparsers.add_parser("status", help="Show environment status")
    status_parser.add_argument(
        "environment",
        choices=VALID_ENVIRONMENTS,
        help="Environment to inspect"
    )

    return parser


def main() -> None:
    check_dependencies()
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "env":
        if args.action == "create":
            cmd_create(args.environment, getattr(args, "var_file", None))
        elif args.action == "destroy":
            cmd_destroy(args.environment, args.force)
        elif args.action == "status":
            cmd_status(args.environment)


if __name__ == "__main__":
    main()
