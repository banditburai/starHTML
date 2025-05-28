#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    print_error "Not in a git repository"
    exit 1
fi

# Check if working directory is clean
if ! git diff-index --quiet HEAD --; then
    print_error "Working directory is not clean. Please commit your changes first."
    exit 1
fi

# Get the bump type from argument
BUMP_TYPE=${1:-patch}

if [[ ! "$BUMP_TYPE" =~ ^(major|minor|patch)$ ]]; then
    print_error "Invalid bump type. Use: major, minor, or patch"
    echo "Usage: $0 [major|minor|patch]"
    exit 1
fi

print_status "Bumping $BUMP_TYPE version..."

# Bump version using bump-my-version
uv run bump-my-version bump $BUMP_TYPE

# Get the new version
NEW_VERSION=$(uv run bump-my-version show current_version)

print_status "Version bumped to $NEW_VERSION"

# Push the changes and tags
print_status "Pushing changes and tags to GitHub..."
git push origin main
git push origin --tags

print_status "Release process initiated!"
print_status "GitHub Actions will now:"
print_status "  1. Create a GitHub release for v$NEW_VERSION"
print_status "  2. Build and publish the package to PyPI"
print_status ""
print_status "Check the Actions tab on GitHub to monitor progress." 