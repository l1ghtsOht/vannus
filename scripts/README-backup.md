# Vannus Nightly Backup — Setup Guide

**Status (May 6, 2026):** ✅ AWS infrastructure provisioned (bucket, IAM user, billing alert). ✅ Backup script tested end-to-end against the production bucket — 3 files uploaded successfully. ⏳ **Pending only:** Railway env vars set + cron job scheduled, both blocked on Railway access. See `~/Desktop/vannus-jason-railway-handoff.md` for the env var list and cron command.

**Production resources (do NOT change):**
- Bucket: `vannus-praxis-backups-813724788137-us-east-2-an`
- Region: `us-east-2` (Ohio)
- IAM user: `vannus-backup-writer` (bucket-scoped policy)
- Account: `813724788137` (Drake / PRAXIS AI LLC)

---

## What gets backed up

- `praxis/tools.db` — SQLite catalog + `llm_cost_events` table
- `praxis/feedback.json` — user feedback log
- `praxis/usage.json` — popularity counters

**Not** backed up: `.env`, source code (in git), `__pycache__`, `node_modules`.

---

## One-time setup (already done as of May 6, 2026)

Steps 1–2 below are **already complete** in Drake's AWS account. They're documented here for re-creation in a fresh AWS account if ever needed (e.g., DR migration, account rotation).

### 1. S3 bucket (already created)

The actual bucket name was set during console creation:
`vannus-praxis-backups-813724788137-us-east-2-an` in `us-east-2`.

To recreate from scratch:

```
aws s3 mb s3://<your-bucket-name> --region us-east-2
aws s3api put-bucket-versioning --bucket <your-bucket-name> \
  --versioning-configuration Status=Enabled
aws s3api put-public-access-block --bucket <your-bucket-name> \
  --public-access-block-configuration \
  "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
```

Then add a 30-day lifecycle rule (`expire-old-backups`) via Console → Management tab.

### 2. IAM user (already created: `vannus-backup-writer`)

Inline policy `vannus-backup-s3-access`:

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": ["s3:PutObject", "s3:GetObject", "s3:ListBucket", "s3:DeleteObject"],
    "Resource": [
      "arn:aws:s3:::vannus-praxis-backups-813724788137-us-east-2-an",
      "arn:aws:s3:::vannus-praxis-backups-813724788137-us-east-2-an/*"
    ]
  }]
}
```

### 3. Railway env vars (PENDING — Jason or Drake to set when Railway access is sorted)

```
AWS_ACCESS_KEY_ID            = <from Drake's 1Password — AKIA... format>
AWS_SECRET_ACCESS_KEY        = <from 1Password>
AWS_REGION                   = us-east-2
VANNUS_S3_BACKUP_BUCKET      = vannus-praxis-backups-813724788137-us-east-2-an
VANNUS_BACKUP_RETENTION_DAYS = 30
VANNUS_SLACK_BACKUP_WEBHOOK  = https://hooks.slack.com/services/...   (optional)
```

### 4. Test locally

```
python3 scripts/backup_to_s3.py --dry-run     # report only, nothing uploaded
python3 scripts/backup_to_s3.py --backup      # actually back up
python3 scripts/backup_to_s3.py --prune       # delete >30-day-old backups
python3 scripts/backup_to_s3.py               # full nightly run
```

### 5. Schedule it

**On Railway** (cron via Railway's cron-job feature):
- Schedule: `15 3 * * *` (03:15 UTC daily)
- Command: `python3 scripts/backup_to_s3.py`

**On a Linux server** (system cron):
```
15 3 * * * cd /path/to/vannus && /usr/bin/python3 scripts/backup_to_s3.py >> /var/log/vannus-backup.log 2>&1
```

**On macOS** (launchd) for local dev backup:
```
~/Library/LaunchAgents/co.vannus.backup.plist
```

(Schedule it for whenever your laptop is awake, e.g., 3 PM if you keep it on a desk.)

---

## Cost

**Through November 6, 2026:** $0 (AWS Free Tier covers it — 5 GB storage, 2K PUTs/month, 20K GETs/month — backup uses ≪1% of any limit). Drake also has $100 in account credits.

**After Nov 6, 2026** (S3 Standard pricing in `us-east-2`):
- Actual measured volume: ~221 KB per night × 3 files (tools.db 213K + feedback.json 7K + usage.json 1K)
- 30-day rolling: ~6.6 MB total (with versioning enabled, slightly more)
- Storage: ~$0.023/GB/month → **$0.00015/month**
- PUT requests: 3 PUTs/night × 30 = 90/month × $0.005/1K → **$0.00045/month**
- DELETE requests: free
- Egress: $0 unless restoring

**Total real cost after free tier: under $0.001/month** (one tenth of a cent). Restore-time egress is the only meaningful cost vector and only kicks in during disaster recovery.

DB will grow as Room ships and paying users hit the catalog (`llm_cost_events` table). Even at 100 MB/file, monthly cost stays under $0.10.

---

## Restore procedure (if disaster strikes)

```
# 1. Find the latest backup date
aws s3 ls s3://vannus-praxis-backups-813724788137-us-east-2-an/backups/ --region us-east-2 | tail -5

# 2. Download all files from the chosen date
aws s3 cp s3://vannus-praxis-backups-813724788137-us-east-2-an/backups/2026-05-30/ ./restored/ --recursive --region us-east-2

# 3. Replace runtime files
cp restored/tools.db praxis/tools.db
cp restored/feedback.json praxis/feedback.json
cp restored/usage.json praxis/usage.json

# 4. Restart the app (Railway will redeploy on push, or just bounce the service)
```

Test the restore procedure once when the bucket is alive — restore-untested backups tend to be unrestoreable in real disasters.

---

## Failure modes & monitoring

The script exits non-zero on errors. Hook the cron failure into:
- Railway's email notifications (if cron fails 3+ times)
- The `VANNUS_SLACK_BACKUP_WEBHOOK` for live status posts
- A weekly check of `aws s3 ls s3://vannus-praxis-backups-813724788137-us-east-2-an/backups/ --region us-east-2` to confirm yesterday's backup landed

Common failure patterns (all surface in script logs):
- Expired AWS credentials → rotate, update Railway env vars
- Bucket policy too restrictive → check the IAM inline policy
- File too large (after Room ships and DB grows) → consider gzip before upload
- Network blip → script retries naturally on next cron tick

---

## When to upgrade this script

Trigger conditions for revisiting:
- DB size > 100 MB → add gzip compression before upload (saves ~70%)
- Backup count > 200 (after 6+ months) → consider lifecycle rule for cold storage
- First real disaster recovery → document what worked, what didn't, what was missing
- Adding new persistence layers (e.g., Redis cache, vector DB) → extend `BACKUP_TARGETS`

---

*Owner: Drake Schreiber. Pre-launch blocker — schedule this before first paid user.*
