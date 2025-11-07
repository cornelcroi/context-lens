#!/bin/bash
# Installation script for MCP Knowledge Base Server

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored messages
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Display banner
echo ""
echo "=============================================="
echo "  MCP Knowledge Base Server - Installation"
echo "=============================================="
echo ""

# Check Python version
print_step "Checking Python installation..."
if ! command_exists python3; then
    print_error "Python 3 is not installed"
    print_info "Please install Python 3.8 or higher from https://www.python.org/"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
print_info "Found Python $PYTHON_VERSION"

# Check Python version is 3.8+
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
    print_error "Python 3.8 or higher is required (found $PYTHON_VERSION)"
    exit 1
fi

# Check pip
print_step "Checking pip installation..."
if ! command_exists pip3; then
    print_error "pip3 is not installed"
    print_info "Please install pip3"
    exit 1
fi

print_info "Found pip $(pip3 --version | cut -d' ' -f2)"

# Ask for installation type
echo ""
print_step "Select installation type:"
echo "  1) Development installation (editable, with dev dependencies)"
echo "  2) Production installation (standard)"
echo ""
read -p "Enter choice [1-2]: " INSTALL_TYPE

case $INSTALL_TYPE in
    1)
        print_info "Installing in development mode..."
        INSTALL_CMD="pip3 install -r requirements-dev.txt && pip3 install -e ."
        ;;
    2)
        print_info "Installing in production mode..."
        INSTALL_CMD="pip3 install -r requirements.txt && pip3 install -e ."
        ;;
    *)
        print_error "Invalid choice"
        exit 1
        ;;
esac

# Create virtual environment option
echo ""
read -p "Create a virtual environment? [y/N]: " CREATE_VENV

if [[ $CREATE_VENV =~ ^[Yy]$ ]]; then
    print_step "Creating virtual environment..."
    
    if [ -d "venv" ]; then
        print_warn "Virtual environment already exists"
        read -p "Remove and recreate? [y/N]: " RECREATE_VENV
        if [[ $RECREATE_VENV =~ ^[Yy]$ ]]; then
            rm -rf venv
            python3 -m venv venv
            print_info "Virtual environment recreated"
        fi
    else
        python3 -m venv venv
        print_info "Virtual environment created"
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    print_info "Virtual environment activated"
fi

# Upgrade pip
print_step "Upgrading pip..."
pip3 install --upgrade pip

# Install package
print_step "Installing MCP Knowledge Base Server..."
eval $INSTALL_CMD

# Verify installation
print_step "Verifying installation..."
if command_exists mcp-knowledge-base; then
    VERSION=$(mcp-knowledge-base --version 2>&1 | grep -oP '\d+\.\d+\.\d+' || echo "unknown")
    print_info "Installation successful! Version: $VERSION"
else
    print_error "Installation verification failed"
    exit 1
fi

# Create directories
print_step "Creating directories..."
mkdir -p logs models data

# Copy example config
if [ ! -f "config.yaml" ]; then
    print_step "Creating default configuration..."
    cp config.example.yaml config.yaml
    print_info "Created config.yaml from example"
else
    print_warn "config.yaml already exists, skipping"
fi

# Make scripts executable
print_step "Setting up scripts..."
chmod +x scripts/*.sh
print_info "Scripts are now executable"

# Display next steps
echo ""
echo "=============================================="
echo "  Installation Complete!"
echo "=============================================="
echo ""
print_info "Next steps:"
echo ""
echo "  1. Review configuration:"
echo "     ${BLUE}cat config.yaml${NC}"
echo ""
echo "  2. Start the server:"
echo "     ${BLUE}mcp-knowledge-base${NC}"
echo ""
echo "  3. Or use the startup script:"
echo "     ${BLUE}./scripts/start_server.sh${NC}"
echo ""
echo "  4. View help:"
echo "     ${BLUE}mcp-knowledge-base --help${NC}"
echo ""
echo "  5. Check configuration:"
echo "     ${BLUE}mcp-knowledge-base --show-config${NC}"
echo ""

if [[ $CREATE_VENV =~ ^[Yy]$ ]]; then
    print_warn "Remember to activate the virtual environment:"
    echo "     ${BLUE}source venv/bin/activate${NC}"
    echo ""
fi

print_info "Documentation:"
echo "  - Quick Start: docs/QUICKSTART.md"
echo "  - Deployment: docs/DEPLOYMENT.md"
echo "  - Error Handling: docs/ERROR_HANDLING.md"
echo ""

print_info "For help and support:"
echo "  - GitHub: https://github.com/example/mcp-knowledge-base"
echo "  - Issues: https://github.com/example/mcp-knowledge-base/issues"
echo ""
