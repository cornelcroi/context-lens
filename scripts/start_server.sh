#!/bin/bash
# Startup script for MCP Knowledge Base Server

set -e

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Default values
CONFIG_FILE=""
LOG_LEVEL="INFO"
LOG_DIR="./logs"
DB_PATH=""
SHOW_CONFIG=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Print colored message
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Display usage
usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Start the MCP Knowledge Base Server with optional configuration.

OPTIONS:
    -c, --config FILE       Path to configuration file
    -l, --log-level LEVEL   Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    -d, --log-dir DIR       Directory for log files
    -b, --db-path PATH      Path to LanceDB database
    -s, --show-config       Display configuration and exit
    -h, --help              Display this help message

EXAMPLES:
    # Start with default configuration
    $0

    # Start with custom config file
    $0 --config config.yaml

    # Start with debug logging
    $0 --log-level DEBUG

    # Show configuration without starting
    $0 --show-config

EOF
    exit 0
}

# Parse command-line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -c|--config)
            CONFIG_FILE="$2"
            shift 2
            ;;
        -l|--log-level)
            LOG_LEVEL="$2"
            shift 2
            ;;
        -d|--log-dir)
            LOG_DIR="$2"
            shift 2
            ;;
        -b|--db-path)
            DB_PATH="$2"
            shift 2
            ;;
        -s|--show-config)
            SHOW_CONFIG=true
            shift
            ;;
        -h|--help)
            usage
            ;;
        *)
            print_error "Unknown option: $1"
            usage
            ;;
    esac
done

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed or not in PATH"
    exit 1
fi

# Check if mcp-knowledge-base is installed
if ! command -v mcp-knowledge-base &> /dev/null; then
    print_error "mcp-knowledge-base is not installed"
    print_info "Install it with: pip install -e ."
    exit 1
fi

# Build command
CMD="mcp-knowledge-base"

if [ -n "$CONFIG_FILE" ]; then
    if [ ! -f "$CONFIG_FILE" ]; then
        print_error "Configuration file not found: $CONFIG_FILE"
        exit 1
    fi
    CMD="$CMD --config $CONFIG_FILE"
fi

if [ -n "$LOG_LEVEL" ]; then
    CMD="$CMD --log-level $LOG_LEVEL"
fi

if [ -n "$LOG_DIR" ]; then
    CMD="$CMD --log-dir $LOG_DIR"
fi

if [ -n "$DB_PATH" ]; then
    CMD="$CMD --db-path $DB_PATH"
fi

if [ "$SHOW_CONFIG" = true ]; then
    CMD="$CMD --show-config"
fi

# Display startup information
print_info "Starting MCP Knowledge Base Server..."
print_info "Command: $CMD"

# Create necessary directories
if [ "$SHOW_CONFIG" = false ]; then
    mkdir -p "$LOG_DIR"
    print_info "Log directory: $LOG_DIR"
fi

# Run the server
print_info "Executing server..."
exec $CMD
