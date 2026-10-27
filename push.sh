#!/bin/bash
# Usage: ./push.sh https://github.com/<username>/KumbhSafe.git
set -e
[ -z "$1" ] && { echo "Usage: ./push.sh <repo-url>"; exit 1; }
git init
git add .
git commit -m "Initial commit: KumbhSafe prototype"
git branch -M main
git remote add origin "$1"
git push -u origin main
