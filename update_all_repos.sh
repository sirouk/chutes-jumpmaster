#!/bin/bash

# Script to update all chutes sub-repositories
# Performs git fetch and git pull on each sub-repository

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "=== Chutes Sub-repositories Update Script ==="
echo "Base directory: $SCRIPT_DIR"
echo ""

# List of sub-repositories to update
REPOS=(
    "chutes"
    "chutes-api"
    "chutes-web"
    "chutes-miner"
    "chutes-e2ee-transport"
    "sek8s"
)

SUCCESS_COUNT=0
FAILURE_COUNT=0
SKIPPED_COUNT=0

for REPO in "${REPOS[@]}"; do
    REPO_PATH="$SCRIPT_DIR/$REPO"
    
    if [ ! -d "$REPO_PATH" ]; then
        echo "[SKIP] $REPO - Directory does not exist"
        ((SKIPPED_COUNT++))
        continue
    fi
    
    # Check if this is a git repository
    if [ ! -d "$REPO_PATH/.git" ]; then
        echo "[SKIP] $REPO - Not a git repository"
        ((SKIPPED_COUNT++))
        continue
    fi
    
    echo "[START] $REPO"
    
    # Get current branch
    CURRENT_BRANCH=$(cd "$REPO_PATH" && git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
    
    # For submodules, use simple git pull without rebase
    # Rebase can cause divergence from the parent repo's expected commit
    if cd "$REPO_PATH" && git pull 2>&1; then
        echo "[UPDATED] $REPO (branch: $CURRENT_BRANCH)"
        ((SUCCESS_COUNT++))
    else
        echo "[FAILED] $REPO - git pull failed"
        ((FAILURE_COUNT++))
    fi
    
    echo ""
done

echo "=== Update Summary ==="
echo "Success: $SUCCESS_COUNT"
echo "Failed: $FAILURE_COUNT"
echo "Skipped: $SKIPPED_COUNT"

if [ $FAILURE_COUNT -gt 0 ]; then
    echo ""
    echo "Some repositories failed to update. Please check the output above."
    exit 1
fi

echo ""
echo "All repositories updated successfully!"
