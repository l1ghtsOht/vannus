#!/usr/bin/env python3
"""
auto_push.py — Watch for git changes and automatically commit + push.

Usage:
    python auto_push.py                  # check every 30 seconds
    python auto_push.py --interval 60    # check every 60 seconds
    python auto_push.py --message "wip"  # custom commit message prefix
    python auto_push.py --dry-run        # print what would happen, don't push
"""

import argparse
import datetime
import subprocess
import sys
import time
import os

REPO_DIR = os.path.dirname(os.path.abspath(__file__))


def run(cmd: list[str], capture: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        cwd=REPO_DIR,
        capture_output=capture,
        text=True,
    )


def has_changes() -> bool:
    """Return True if the working tree or index has anything to commit."""
    result = run(["git", "status", "--porcelain"])
    return bool(result.stdout.strip())


def current_branch() -> str:
    result = run(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    return result.stdout.strip()


def auto_commit_push(message_prefix: str, dry_run: bool) -> bool:
    """Stage all changes, commit, and push.  Returns True on success."""
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    msg = f"{message_prefix}: {ts}"

    if dry_run:
        print(f"[dry-run] would commit: {msg!r}")
        return True

    # Stage everything
    stage = run(["git", "add", "-A"])
    if stage.returncode != 0:
        print(f"[auto-push] ERROR staging: {stage.stderr.strip()}", flush=True)
        return False

    # Commit
    commit = run(["git", "commit", "-m", msg])
    if commit.returncode != 0:
        # Nothing to commit is not an error
        if "nothing to commit" in commit.stdout + commit.stderr:
            return True
        print(f"[auto-push] ERROR committing: {commit.stderr.strip()}", flush=True)
        return False

    print(f"[auto-push] committed: {msg}", flush=True)

    # Pull (rebase) before pushing to avoid rejection when remote is ahead
    branch = current_branch()
    pull = run(["git", "pull", "--rebase", "origin", branch])
    if pull.returncode != 0:
        print(f"[auto-push] ERROR pulling (rebase): {pull.stderr.strip()}", flush=True)
        return False

    # Push
    push = run(["git", "push", "origin", branch])
    if push.returncode != 0:
        print(f"[auto-push] ERROR pushing: {push.stderr.strip()}", flush=True)
        return False

    print(f"[auto-push] pushed → origin/{branch}", flush=True)
    return True


def main():
    parser = argparse.ArgumentParser(description="Auto-commit and push git changes.")
    parser.add_argument("--interval", type=int, default=30, help="Seconds between checks (default: 30)")
    parser.add_argument("--message", default="auto", help="Commit message prefix (default: auto)")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without executing")
    parser.add_argument("--once", action="store_true", help="Run once and exit (no loop)")
    args = parser.parse_args()

    branch = current_branch()
    print(f"[auto-push] watching {REPO_DIR}", flush=True)
    print(f"[auto-push] branch: {branch}  interval: {args.interval}s  prefix: {args.message!r}", flush=True)
    if args.dry_run:
        print("[auto-push] DRY RUN — no changes will be committed", flush=True)

    while True:
        try:
            if has_changes():
                auto_commit_push(args.message, args.dry_run)
            else:
                print(f"[auto-push] {datetime.datetime.now().strftime('%H:%M:%S')} — no changes", flush=True)
        except KeyboardInterrupt:
            print("\n[auto-push] stopped.", flush=True)
            sys.exit(0)
        except Exception as exc:
            print(f"[auto-push] unexpected error: {exc}", flush=True)

        if args.once:
            break

        try:
            time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\n[auto-push] stopped.", flush=True)
            sys.exit(0)


if __name__ == "__main__":
    main()
