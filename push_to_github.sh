#!/usr/bin/env bash
set -e

echo "Committing and pushing to https://github.com/ghkrknkp/Solana.git..."
git add .
git commit -m "Complete Solana Substreams transfer extraction for blocks 385870151-385870156" || true
git branch -M main || true
git push -u origin main
echo "Successfully pushed to GitHub!"

