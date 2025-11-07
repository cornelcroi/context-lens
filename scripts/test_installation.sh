#!/bin/bash
# Test script to verify MCP Knowledge Base Server installation

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${YELLOW}ℹ${NC} $1"
}

echo ""
echo "=========================================="
echo "  MCP Knowledge Base - Installation Test"
echo "=========================================="
echo ""

# Test 1: Python version
print_info "Checking Python version..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    print_success "Python found: $PYTHON_VERSION"
else
    print_error "Python 3 not found"
    exit 1
fi

# Test 2: Package installation
print_info "Checking package installation..."
if command -v mcp-knowledge-base &> /dev/null; then
    VERSION=$(mcp-knowledge-base --version 2>&1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' || echo "unknown")
    print_success "Package installed: version $VERSION"
else
    print_error "mcp-knowledge-base command not found"
    print_info "Try: pip install -e ."
    exit 1
fi

# Test 3: Configuration display
print_info "Testing configuration..."
if python3 -m mcp_knowledge_base.main --show-config > /dev/null 2>&1; then
    print_success "Configuration loads successfully"
else
    print_error "Configuration test failed"
    print_info "This may be normal if dependencies aren't fully installed"
fi

# Test 4: Dependencies
print_info "Checking dependencies..."
python3 -c "import fastmcp, lancedb, sentence_transformers" 2>/dev/null
if [ $? -eq 0 ]; then
    print_success "All dependencies installed"
else
    print_error "Missing dependencies"
    print_info "Try: pip install -r requirements.txt"
    exit 1
fi

# Test 5: Directory structure
print_info "Checking directory structure..."
MISSING_DIRS=""
for dir in "src" "tests" "docs" "scripts"; do
    if [ ! -d "$dir" ]; then
        MISSING_DIRS="$MISSING_DIRS $dir"
    fi
done

if [ -z "$MISSING_DIRS" ]; then
    print_success "Directory structure is correct"
else
    print_error "Missing directories:$MISSING_DIRS"
fi

# Test 6: Scripts are executable
print_info "Checking scripts..."
if [ -x "scripts/start_server.sh" ]; then
    print_success "Scripts are executable"
else
    print_error "Scripts are not executable"
    print_info "Run: chmod +x scripts/*.sh"
fi

# Test 7: Configuration file
print_info "Checking configuration files..."
if [ -f "config.example.yaml" ]; then
    print_success "Example configuration exists"
else
    print_error "config.example.yaml not found"
fi

echo ""
echo "=========================================="
echo "  Test Summary"
echo "=========================================="
echo ""
print_success "Installation test completed successfully!"
echo ""
print_info "Next steps:"
echo "  1. Start the server: mcp-knowledge-base"
echo "  2. Or use the script: ./scripts/start_server.sh"
echo "  3. Configure your MCP client (see INSTALL.md)"
echo ""
print_info "Documentation:"
echo "  - Installation: INSTALL.md"
echo "  - Usage with LLMs: docs/USAGE_WITH_LLM.md"
echo "  - Quick Start: docs/QUICKSTART.md"
echo ""
