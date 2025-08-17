#!/usr/bin/env bash
set -euo pipefail

# Configuration
BUILD_DIR="site"       # local folder containing static site to publish
REMOTE="origin"        # The name of the remote repository (usually "origin")
TARGET_BRANCH="gh-pages" # The branch to push the subtree to

if [ ! -d "$BUILD_DIR" ]; then
  echo "Error: build dir '$BUILD_DIR' not found. Put your static files there."
  exit 1
fi

# Ensure working tree is committed (subtree requires the files tracked)
git add -A
git commit -m "chore: pre-deploy commit" || echo "No changes to commit"

# Push subtree to gh-pages
git subtree push --prefix "$BUILD_DIR" "$REMOTE" "$TARGET_BRANCH"
