#!/bin/bash

echo "🧪 Local Release Process Test"
echo "============================="

# Get current version from pyproject.toml
CURRENT_VERSION=$(grep "^version = " pyproject.toml | cut -d'"' -f2)
echo "Current version from pyproject.toml: '$CURRENT_VERSION'"

# Debug: Show the raw grep output
echo "Raw grep output:"
grep "^version = " pyproject.toml

# Validate current version format
if [ -z "$CURRENT_VERSION" ]; then
    echo "❌ Error: Could not extract version from pyproject.toml"
    echo "Content of pyproject.toml (first 10 lines):"
    head -10 pyproject.toml
    exit 1
fi

if ! [[ "$CURRENT_VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "❌ Error: Current version '$CURRENT_VERSION' is not in X.Y.Z format"
    exit 1
fi

# Split version into components
IFS='.' read -r MAJOR MINOR PATCH <<< "$CURRENT_VERSION"
echo "Version components: MAJOR=$MAJOR, MINOR=$MINOR, PATCH=$PATCH"

# Test each release type
for RELEASE_TYPE in patch minor major; do
    echo ""
    echo "Testing $RELEASE_TYPE release:"
    
    case $RELEASE_TYPE in
        major)
            NEW_MAJOR=$((MAJOR + 1))
            NEW_MINOR=0
            NEW_PATCH=0
            ;;
        minor)
            NEW_MAJOR=$MAJOR
            NEW_MINOR=$((MINOR + 1))
            NEW_PATCH=0
            ;;
        patch)
            NEW_MAJOR=$MAJOR
            NEW_MINOR=$MINOR
            NEW_PATCH=$((PATCH + 1))
            ;;
    esac
    
    NEW_VERSION="$NEW_MAJOR.$NEW_MINOR.$NEW_PATCH"
    echo "  $CURRENT_VERSION → $NEW_VERSION (tag: v$NEW_VERSION)"
done

echo ""
echo "✅ Version parsing and calculation working correctly!"