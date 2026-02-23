#!/bin/bash
# Daily OpenClaw Backup Script

WORKDIR="/data/.openclaw/workspace"
cd "$WORKDIR" || exit 1

DATE=$(date '+%Y-%m-%d')
TIME=$(date '+%H:%M')

# Check if there are changes
git add -A 2>/dev/null
if git diff --cached --quiet; then
    echo "[$DATE $TIME] No changes to backup"
    exit 0
fi

# Commit and push
git commit -m "Daily backup: $DATE" 2>/dev/null
if [ $? -eq 0 ]; then
    git push origin master 2>/dev/null
    echo "[$DATE $TIME] Backup pushed successfully"
else
    echo "[$DATE $TIME] Commit failed"
    exit 1
fi
