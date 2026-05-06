#!/usr/bin/env python3
"""
backup_to_s3.py — Nightly backup of Vannus runtime data to S3.

What gets backed up:
    - praxis/tools.db        (SQLite catalog + cost_events)
    - praxis/feedback.json   (user feedback log)
    - praxis/usage.json      (popularity counters)

What does NOT get backed up:
    - .env / config.json     (secrets, never)
    - source code            (already in git)
    - __pycache__            (regenerable)

Schedule: nightly at 03:15 UTC (Railway cron or system cron).
Retention: 30 days. Old backups auto-deleted by this script
when STAGE=prune is set.

Required env vars:
    AWS_ACCESS_KEY_ID
    AWS_SECRET_ACCESS_KEY
    AWS_REGION                (e.g. "us-east-1")
    VANNUS_S3_BACKUP_BUCKET   (e.g. "vannus-backups")

Optional:
    VANNUS_BACKUP_RETENTION_DAYS  (default: 30)
    VANNUS_SLACK_BACKUP_WEBHOOK   (post status to Slack)

Usage:
    python3 scripts/backup_to_s3.py            # full run: backup + prune
    python3 scripts/backup_to_s3.py --dry-run  # report what would happen
    python3 scripts/backup_to_s3.py --backup   # backup only
    python3 scripts/backup_to_s3.py --prune    # prune old backups only

Cost: trivial. ~5 MB/day uploaded to S3 Standard ≈ $0.12/year storage,
$0 egress unless restoring. Well under the $5/mo Drake budgeted in
the master plan.
"""

import argparse
import json
import logging
import os
import sys
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("backup_to_s3")


REPO_ROOT = Path(__file__).resolve().parent.parent
PRAXIS_DIR = REPO_ROOT / "praxis"

BACKUP_TARGETS = [
    PRAXIS_DIR / "tools.db",
    PRAXIS_DIR / "feedback.json",
    PRAXIS_DIR / "usage.json",
]


def _slack_post(text: str) -> None:
    url = os.environ.get("VANNUS_SLACK_BACKUP_WEBHOOK", "").strip()
    if not url:
        return
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps({"text": text}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        urllib.request.urlopen(req, timeout=5).read()
    except Exception as e:  # don't fail the backup if Slack errors
        log.warning("slack post failed: %s", e)


def _get_s3_client():
    try:
        import boto3  # type: ignore
    except ImportError:
        log.error(
            "boto3 not installed. Run: pip install boto3 "
            "(or add to requirements.txt and redeploy)"
        )
        sys.exit(2)
    return boto3.client("s3", region_name=os.environ.get("AWS_REGION", "us-east-1"))


def backup(dry_run: bool = False) -> dict:
    bucket = os.environ.get("VANNUS_S3_BACKUP_BUCKET", "").strip()
    if not bucket:
        log.error("VANNUS_S3_BACKUP_BUCKET env var not set")
        sys.exit(2)

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    summary = {"date": today, "uploaded": [], "skipped": [], "errors": []}

    if dry_run:
        log.info("DRY RUN — would back up to s3://%s/backups/%s/", bucket, today)
        for f in BACKUP_TARGETS:
            if f.exists():
                summary["uploaded"].append({"file": str(f.name), "size": f.stat().st_size, "dry": True})
                log.info("  would upload: %s (%d bytes)", f.name, f.stat().st_size)
            else:
                summary["skipped"].append({"file": str(f.name), "reason": "not present"})
                log.info("  would skip: %s (not present)", f.name)
        return summary

    s3 = _get_s3_client()

    for f in BACKUP_TARGETS:
        if not f.exists():
            log.info("skip (not present): %s", f.name)
            summary["skipped"].append({"file": f.name, "reason": "not present"})
            continue
        key = f"backups/{today}/{f.name}"
        try:
            s3.upload_file(str(f), bucket, key)
            size = f.stat().st_size
            log.info("uploaded: s3://%s/%s (%d bytes)", bucket, key, size)
            summary["uploaded"].append({"file": f.name, "key": key, "size": size})
        except Exception as e:
            log.error("upload failed for %s: %s", f.name, e)
            summary["errors"].append({"file": f.name, "error": str(e)})

    return summary


def prune_old_backups(retention_days: int = 30, dry_run: bool = False) -> dict:
    bucket = os.environ.get("VANNUS_S3_BACKUP_BUCKET", "").strip()
    if not bucket:
        log.error("VANNUS_S3_BACKUP_BUCKET env var not set")
        sys.exit(2)

    cutoff = (datetime.now(timezone.utc) - timedelta(days=retention_days)).date()
    summary = {"cutoff": cutoff.isoformat(), "deleted": [], "kept": [], "errors": []}

    s3 = _get_s3_client()

    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix="backups/"):
        for obj in page.get("Contents", []) or []:
            key = obj["Key"]
            # Expected key format: backups/YYYY-MM-DD/filename
            parts = key.split("/", 2)
            if len(parts) < 3:
                continue
            date_str = parts[1]
            try:
                key_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                continue
            if key_date < cutoff:
                if dry_run:
                    log.info("DRY RUN — would delete: %s (date %s)", key, key_date)
                    summary["deleted"].append({"key": key, "date": str(key_date), "dry": True})
                else:
                    try:
                        s3.delete_object(Bucket=bucket, Key=key)
                        log.info("deleted: %s", key)
                        summary["deleted"].append({"key": key, "date": str(key_date)})
                    except Exception as e:
                        log.error("delete failed for %s: %s", key, e)
                        summary["errors"].append({"key": key, "error": str(e)})
            else:
                summary["kept"].append({"key": key, "date": str(key_date)})

    return summary


def main():
    ap = argparse.ArgumentParser(description="Vannus S3 backup")
    ap.add_argument("--dry-run", action="store_true", help="report only, do nothing")
    ap.add_argument("--backup", action="store_true", help="backup only (skip prune)")
    ap.add_argument("--prune", action="store_true", help="prune only (skip backup)")
    args = ap.parse_args()

    do_backup = not args.prune
    do_prune = not args.backup

    retention = int(os.environ.get("VANNUS_BACKUP_RETENTION_DAYS", "30"))

    overall = {"backup": None, "prune": None}
    try:
        if do_backup:
            overall["backup"] = backup(dry_run=args.dry_run)
        if do_prune:
            overall["prune"] = prune_old_backups(retention_days=retention, dry_run=args.dry_run)

        # Slack summary
        bk = overall["backup"] or {}
        pr = overall["prune"] or {}
        text = (
            f"📦 Vannus backup ({bk.get('date', '')}): "
            f"{len(bk.get('uploaded', []))} uploaded, "
            f"{len(bk.get('skipped', []))} skipped, "
            f"{len(bk.get('errors', []))} errors. "
            f"Pruned {len(pr.get('deleted', []))} > {retention} days old."
        )
        log.info(text)
        if not args.dry_run:
            _slack_post(text)

        # Exit non-zero if any errors
        all_errors = (
            (overall["backup"] or {}).get("errors", [])
            + (overall["prune"] or {}).get("errors", [])
        )
        if all_errors:
            log.warning("completed with %d errors", len(all_errors))
            sys.exit(1)

        log.info("backup complete")
    except KeyboardInterrupt:
        log.warning("interrupted")
        sys.exit(130)
    except Exception as e:
        log.exception("unhandled error in backup pipeline: %s", e)
        if not args.dry_run:
            _slack_post(f"🚨 Vannus backup failed with unhandled error: {type(e).__name__}: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
