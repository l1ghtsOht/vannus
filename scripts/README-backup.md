# Vannus Nightly Backup — Setup Guide

**Status (May 2026):** scaffold only — `backup_to_s3.py` is written and tested in dry-run mode but is **not yet scheduled** in production. Schedule it before the first paying Pro+ user lands. Prereq: AWS account with S3 bucket created.

---

## What gets backed up

- `praxis/tools.db` — SQLite catalog + `llm_cost_events` table
- `praxis/feedback.json` — user feedback log
- `praxis/usage.json` — popularity counters

**Not** backed up: `.env`, source code (in git), `__pycache__`, `node_modules`.

---

## One-time setup (10-15 min)

### 1. Create the S3 bucket

```
aws s3 mb s3://vannus-backups --region us-east-1
aws s3api put-bucket-versioning --bucket vannus-backups \
  --versioning-configuration Status=Enabled
aws s3api put-public-access-block --bucket vannus-backups \
  --public-access-block-configuration \
  "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
```

The bucket should be private. Versioning protects against accidental script bugs that delete real data.

### 2. Create an IAM user with minimal permissions

```
aws iam create-user --user-name vannus-backup-bot
aws iam attach-user-policy --user-name vannus-backup-bot --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess
# OR (preferred, narrower) attach an inline policy that only allows
# s3:PutObject, s3:GetObject, s3:DeleteObject, s3:ListBucket on this bucket only.
aws iam create-access-key --user-name vannus-backup-bot
# -> save the AccessKeyId and SecretAccessKey
```

### 3. Add Railway env vars

```
AWS_ACCESS_KEY_ID         = AKIA...
AWS_SECRET_ACCESS_KEY     = ...
AWS_REGION                = us-east-1
VANNUS_S3_BACKUP_BUCKET   = vannus-backups
VANNUS_BACKUP_RETENTION_DAYS = 30
VANNUS_SLACK_BACKUP_WEBHOOK = https://hooks.slack.com/services/...   (optional)
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

S3 Standard pricing (May 2026):
- Storage: ~$0.023/GB/month
- 30 days × 5 MB/day = 150 MB max → **~$0.003/month**
- PUT requests: ~$0.005 per 1K → **3-4 per night = $0**
- DELETE requests: free
- Egress: $0 unless you actually restore

**Total: under $0.05/month. Drake's master plan budgeted $5/mo — actual cost is nothing.**

---

## Restore procedure (if disaster strikes)

```
# 1. Find the latest backup date
aws s3 ls s3://vannus-backups/backups/ | tail -5

# 2. Download all files from the chosen date
aws s3 cp s3://vannus-backups/backups/2026-05-30/ ./restored/ --recursive

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
- A weekly check of `aws s3 ls s3://vannus-backups/backups/` to confirm yesterday's backup landed

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
