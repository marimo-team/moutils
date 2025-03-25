#!/bin/bash
set -e

# Colors and formatting
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color
BOLD='\033[1m'

print_step() {
  echo -e "\n${BOLD}${GREEN}=== $1 ===${NC}\n"
}

print_warning() {
  echo -e "${YELLOW}WARNING: $1${NC}"
}

print_error() {
  echo -e "${RED}ERROR: $1${NC}"
}

confirm() {
  echo -e -n "${BOLD}$1 (y/N) ${NC}"
  read -r response
  [[ "$response" == "y" ]]
}

# Header
echo -e "${BOLD}${GREEN}"
echo "╔════════════════════════════════════╗"
echo "║        moutils release script      ║"
echo "╚════════════════════════════════════╝"
echo -e "${NC}"

# Check if version type is provided
if [ -z "$1" ]; then
  echo -e "\nAvailable version types:"
  # echo "  - major (x.0.0)"
  echo "  - minor (0.x.0)"
  echo "  - patch (0.0.x)"
  print_error "Please specify version type: ./release.sh <minor|patch>"
  exit 1
fi

VERSION_TYPE=$1

# Validate version type
if [[ ! "$VERSION_TYPE" =~ ^(minor|patch)$ ]]; then
  print_error "Invalid version type. Use: minor or patch"
  exit 1
fi

# Check if on main branch
print_step "Checking git branch"
BRANCH=$(git branch --show-current)
if [ "$BRANCH" != "main" ]; then
  print_error "Not on main branch. Current branch: $BRANCH"
  echo "Please run: git checkout main"
  exit 1
fi

# Check git state
print_step "Checking git status"
if [ -n "$(git status --porcelain)" ]; then
  print_error "Git working directory is not clean"
  echo "Please commit or stash your changes first:"
  git status
  exit 1
fi

# Pull latest changes
print_step "Pulling latest changes"
git pull origin main

# Get current version from pyproject.toml
CURRENT_VERSION=$(grep -m 1 'version = ' pyproject.toml | cut -d '"' -f 2)
echo "Current version: $CURRENT_VERSION"

# Calculate new version
if [ "$VERSION_TYPE" == "minor" ]; then
  MAJOR=$(echo $CURRENT_VERSION | cut -d. -f1)
  MINOR=$(echo $CURRENT_VERSION | cut -d. -f2)
  PATCH=0
  NEW_VERSION="$MAJOR.$((MINOR + 1)).$PATCH"
elif [ "$VERSION_TYPE" == "patch" ]; then
  MAJOR=$(echo $CURRENT_VERSION | cut -d. -f1)
  MINOR=$(echo $CURRENT_VERSION | cut -d. -f2)
  PATCH=$(echo $CURRENT_VERSION | cut -d. -f3)
  NEW_VERSION="$MAJOR.$MINOR.$((PATCH + 1))"
fi

# Update version in pyproject.toml
print_step "Updating version"
echo -e "Updating version from $CURRENT_VERSION to $NEW_VERSION\n"
sed -i '' "s/version = \"$CURRENT_VERSION\"/version = \"$NEW_VERSION\"/" pyproject.toml

# Summary and confirmation
echo -e "\n${BOLD}Release Summary:${NC}"
echo "  • New Version: $NEW_VERSION"
echo "  • Files to be committed:"
echo "    - pyproject.toml"

if ! confirm "Proceed with release?"; then
  print_warning "Release cancelled"
  # Revert changes
  sed -i '' "s/version = \"$NEW_VERSION\"/version = \"$CURRENT_VERSION\"/" pyproject.toml
  exit 1
fi

# Commit version change
print_step "Committing version change"
git add pyproject.toml
git commit -m "release: $NEW_VERSION"

# Push changes
if confirm "Push changes to remote?"; then
  git push origin main
  echo -e "${GREEN}✓ Changes pushed successfully${NC}"
fi

# Create and push tag
if confirm "Create and push tag $NEW_VERSION?"; then
  git tag -a "$NEW_VERSION" -m "release: $NEW_VERSION"
  git push origin --tags
  echo -e "${GREEN}✓ Tag pushed successfully${NC}"
fi

# Final success message
echo -e "\n${BOLD}${GREEN}🎉 Release $NEW_VERSION completed successfully! 🎉${NC}\n"
echo -e "${YELLOW}Don't forget to:${NC}"
echo "  1. Monitor the release: https://github.com/marimo-team/moutils/actions/workflows/build.yml"
echo "  2. The package will be automatically published to PyPI via the GitHub workflow"
