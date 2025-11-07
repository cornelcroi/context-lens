#!/bin/bash
# Script to prepare a new release

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_info() {
    echo -e "${YELLOW}ℹ${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

echo ""
echo "=========================================="
echo "  MCP Knowledge Base - Release Preparation"
echo "=========================================="
echo ""

# Check if version is provided
if [ -z "$1" ]; then
    print_error "Version number required"
    echo "Usage: $0 <version>"
    echo "Example: $0 0.1.0"
    exit 1
fi

VERSION=$1
TAG="v$VERSION"

print_info "Preparing release $VERSION"
echo ""

# Check if git is clean
if [ -n "$(git status --porcelain)" ]; then
    print_error "Git working directory is not clean"
    echo "Please commit or stash your changes first"
    exit 1
fi

print_success "Git working directory is clean"

# Check if on main branch
BRANCH=$(git branch --show-current)
if [ "$BRANCH" != "main" ]; then
    print_info "Current branch: $BRANCH"
    read -p "Not on main branch. Continue anyway? [y/N]: " CONTINUE
    if [[ ! $CONTINUE =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Update version in pyproject.toml
print_info "Updating version in pyproject.toml..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    sed -i '' "s/^version = .*/version = \"$VERSION\"/" pyproject.toml
else
    # Linux
    sed -i "s/^version = .*/version = \"$VERSION\"/" pyproject.toml
fi

print_success "Version updated to $VERSION"

# Run tests
print_info "Running tests..."
if pytest tests/ -v; then
    print_success "All tests passed"
else
    print_error "Tests failed"
    exit 1
fi

# Check code formatting
print_info "Checking code formatting..."
if black --check src tests && isort --check-only src tests; then
    print_success "Code formatting is correct"
else
    print_error "Code formatting issues found"
    echo "Run: black src tests && isort src tests"
    exit 1
fi

# Build package
print_info "Building package..."
rm -rf dist/ build/ *.egg-info
python -m build

if [ $? -eq 0 ]; then
    print_success "Package built successfully"
else
    print_error "Package build failed"
    exit 1
fi

# Check package
print_info "Checking package..."
if twine check dist/*; then
    print_success "Package check passed"
else
    print_error "Package check failed"
    exit 1
fi

echo ""
echo "=========================================="
echo "  Release Preparation Complete!"
echo "=========================================="
echo ""

print_info "Next steps:"
echo ""
echo "1. Review changes:"
echo "   ${GREEN}git diff pyproject.toml${NC}"
echo ""
echo "2. Commit version bump:"
echo "   ${GREEN}git add pyproject.toml${NC}"
echo "   ${GREEN}git commit -m \"Bump version to $VERSION\"${NC}"
echo ""
echo "3. Create and push tag:"
echo "   ${GREEN}git tag $TAG${NC}"
echo "   ${GREEN}git push origin main${NC}"
echo "   ${GREEN}git push origin $TAG${NC}"
echo ""
echo "4. GitHub Actions will automatically:"
echo "   - Create a GitHub release"
echo "   - Publish to PyPI"
echo ""
echo "5. Or publish manually:"
echo "   ${GREEN}twine upload dist/*${NC}"
echo ""
